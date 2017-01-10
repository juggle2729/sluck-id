package lucky

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/garyburd/redigo/redis"
	"gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
	"log"
	"strings"
	"sync"
	"time"

	. "github.com/mozilla-services/heka/pipeline"
)

type LuckyOutput struct {
	*LuckyOutputConfig
	Mg       *mgo.Session
	Rd       *redis.Pool
	PackChan chan *PipelinePack
	wg       *sync.WaitGroup
	or       OutputRunner
}

type MongoExport struct {
	UserId int64
	Set    bson.M
	Inc    bson.M
	Data   bson.M
}

type LuckyOutputConfig struct {
	MongoAddr        []string `toml:"mongo_addr"`
	RedisAddr        string   `toml:"redis_addr"`
	ConnectTimeout   uint32   `toml:"connect_timeout"`
	Procs            uint32   `toml:"procs"`
	DbName           string   `toml:"db_name"`
	TotalCollection  string   `toml:"total"`
	DailyCollection  string   `toml: "daily"`
	DeviceCollection string   `toml: "device"`
}

func (o *LuckyOutput) ConfigStruct() interface{} {
	return &LuckyOutputConfig{
		MongoAddr:        []string{"localhost:27017"},
		RedisAddr:        "127.0.0.1:6379",
		ConnectTimeout:   3,
		Procs:            5,
		DbName:           "lucky",
		TotalCollection:  "user_stats",
		DailyCollection:  "daily_stats",
		DeviceCollection: "device_stats",
	}
}

func (o *LuckyOutput) Init(config interface{}) (err error) {
	o.LuckyOutputConfig = config.(*LuckyOutputConfig)
	o.PackChan = make(chan *PipelinePack, int(o.Procs))
	dialInfo := mgo.DialInfo{Addrs: o.MongoAddr,
		Timeout: time.Duration(o.ConnectTimeout) * time.Second}
	if o.Mg, err = mgo.DialWithInfo(&dialInfo); err != nil {
		o.or.LogError(err)
		return err
	}

	o.Rd = &redis.Pool{
		MaxIdle:     3,
		IdleTimeout: 5 * time.Minute,
		Dial: func() (redis.Conn, error) {
			c, err := redis.Dial("tcp", o.RedisAddr)
			if err != nil {
				return nil, errors.New("can't conn to redis")
			}
			return c, nil
		},
		TestOnBorrow: func(c redis.Conn, t time.Time) error {
			_, err := c.Do("PING")
			return err
		},
	}
	conn := o.Rd.Get()
	if _, err := conn.Do("PING"); err != nil {
		return errors.New("can't create redis conn")
	}
	conn.Close()
	return nil
}

func (o *LuckyOutput) Run(or OutputRunner, h PluginHelper) (err error) {
	o.or = or
	o.wg = new(sync.WaitGroup)

	for i := 0; i < int(o.Procs); i++ {
		o.wg.Add(1)
		go save(o)
	}
	for pack := range or.InChan() {
		o.PackChan <- pack
	}
	if o.Mg != nil {
		o.Mg.Close()
	}
	close(o.PackChan)
	o.wg.Wait()
	return nil
}

func save(o *LuckyOutput) {
	var (
		err error
		db  *mgo.Database
	)
	for pack := range o.PackChan {
		session := o.Mg.Copy()
		db = session.DB(o.DbName)
		if err = o.Process(pack, db); err != nil {
			o.or.LogError(err)
			pack.Recycle(NewRetryMessageError(err.Error()))
		} else {
			o.or.UpdateCursor(pack.QueueCursor)
			pack.Recycle(nil)
		}
		session.Close()
	}
	o.wg.Done()
}

func convertTime(data *bson.M) {
	var (
		err error
	)
	for k, v := range *data {
		if strings.HasSuffix(k, "_at") {
			timestamp := v.(string)
			(*data)[k], err = time.Parse("2006-01-02T15:04:05.999999", timestamp)
			if err != nil {
				log.Printf("time %s format wrong", timestamp)
				(*data)[k] = time.Now().UTC()
			}
		}
	}
}

func IsVirtual(userId int64, pool *redis.Pool) (r bool, err error) {
	rd := pool.Get()
	if r, err = redis.Bool(rd.Do("SISMEMBER", "lucky:virtual:account", userId)); err != nil {
		return false, err
	}
	return r, nil
}

func (o *LuckyOutput) saveToRedis(data *MongoExport) (err error) {
	var (
		temp interface{}
		ok   bool
	)
	rd := o.Rd.Get()
	key := fmt.Sprintf("stats:user:%d", data.UserId)
	today := getLocalStr(time.Now())
	dailyKey := fmt.Sprintf("stats:%s:%d", today, data.UserId)
	if temp, ok = data.Inc["win.total"]; ok {
		rd.Do("HINCRBY", key, "total_win", temp)
	}
	if temp, ok = data.Inc["recharge.total"]; ok {
		rd.Do("HINCRBY", key, "total_recharge", temp)
		rd.Do("HINCRBY", dailyKey, "total_recharge", temp)
		rd.Do("EXPIRE", dailyKey, 24*3600)
	}
	if temp, ok = data.Inc["pay.total"]; ok {
		rd.Do("HINCRBY", key, "total_pay", temp)
	}
	if temp, ok = data.Set["win.last_at"]; ok {
		var t time.Time
		if t, ok = temp.(time.Time); ok {
			timestamp := t.Unix()
			rd.Do("HSET", key, "last_win", timestamp)
			rd.Do("HINCRBY", key, "win_count", 1)
		}
	}
	return
}

func getLocalStr(base time.Time) string {
	loc, _ := time.LoadLocation("Asia/Shanghai")
	return base.In(loc).Format("2006-01-02")
}

func (o *LuckyOutput) saveToMongo(data *MongoExport, db *mgo.Database, updated_at time.Time) (err error) {
	insertData := make(map[string]bson.M)
	if len(data.Set) > 0 {
		insertData["$set"] = data.Set
	}
	if len(data.Inc) > 0 {
		insertData["$inc"] = data.Inc
	}
	_, err = db.C(o.TotalCollection).UpsertId(data.UserId, insertData)
	if err != nil {
		if mgo.IsDup(err) {
			_, err = db.C(o.TotalCollection).UpsertId(data.UserId, insertData)
		}
		if err != nil {
			o.or.LogError(err)
		}
	}

	key := fmt.Sprintf("%d-%s", data.UserId, getLocalStr(updated_at))
	insertData["$set"]["user_id"] = data.UserId
	_, err = db.C(o.DailyCollection).UpsertId(key, insertData)
	if err != nil && mgo.IsDup(err) {
		_, err = db.C(o.DailyCollection).UpsertId(key, insertData)
	}
	return
}

func (o *LuckyOutput) trackDevice(data *MongoExport, db *mgo.Database, updated_at time.Time) (err error) {
	var (
		temp interface{}
		aid  string
		ok   bool
	)
	temp = data.Set["aid"]
	if aid, ok = temp.(string); !ok {
		return fmt.Errorf("fail to change aid to string: %v", temp)
	}
	delete(data.Set, "aid")
	insertData := make(map[string]bson.M)
	if data.UserId != 1 {
		data.Set["uid"] = data.UserId
	}
	insertData["$set"] = data.Set
	insertData["$setOnInsert"] = bson.M{"created_at": updated_at}
	_, err = db.C(o.DeviceCollection).UpsertId(aid, insertData)
	if err != nil {
		if mgo.IsDup(err) {
			_, err = db.C(o.DeviceCollection).UpsertId(aid, insertData)
		}
		if err != nil {
			log.Println(err.Error())
		}
	}
	return err
}

func (o *LuckyOutput) CleanupForRestart() {
	return
}

func (o *LuckyOutput) Process(pack *PipelinePack, db *mgo.Database) (err error) {
	var (
		data       MongoExport
		ok         bool
		updated_at time.Time
		temp       interface{}
		msgType    string
	)
	payload := pack.Message.GetPayload()
	if err = json.Unmarshal([]byte(payload), &data); err != nil {
		return err
	}
	if data.UserId == 0 {
		return fmt.Errorf("json unmarshal result userid 0 for %v", payload)
	}

	if temp, ok = data.Data["type"]; ok {
		if msgType, ok = temp.(string); !ok {
			return fmt.Errorf("msg type format error")
		}
	} else {
		return fmt.Errorf("msg type not exist")
	}
	convertTime(&data.Set)
	temp = data.Set["updated_at"]
	if updated_at, ok = temp.(time.Time); !ok {
		return errors.New("can't convert updated time")
	}
	if msgType == "active" {
		// device track
		if temp, ok = data.Set["aid"]; ok {
			o.trackDevice(&data, db, updated_at)
		} else {
			return fmt.Errorf("fail to get aid: %v", data)
		}
	}
	if data.UserId == 1 {
		return nil
	}
	if ok, err = IsVirtual(data.UserId, o.Rd); ok {
		return nil
	}
	if msgType == "win" {
		if temp, ok = data.Set["win.first_price"]; ok {
			result := make(map[string]interface{})
			err = db.C(o.TotalCollection).Find(
				bson.M{"_id": data.UserId}).One(
				&result)
			if err != nil {
				o.or.LogError(err)
			}
			if temp, ok = result["recharge"]; ok {
				var recharged map[string]interface{}
				if recharged, ok = temp.(map[string]interface{}); ok {
					data.Set["win.first_recharged"], ok = recharged["total"]
				}
			}
			if temp, ok = result["pay"]; ok {
				var payed map[string]interface{}
				if payed, ok = temp.(map[string]interface{}); ok {
					data.Set["win.first_payed"], ok = payed["total"]
				}
			}
		}
	}
	if err = o.saveToMongo(&data, db, updated_at); err != nil {
		return err
	}
	if err = o.saveToRedis(&data); err != nil {
		return err
	}
	return
}

func init() {
	RegisterPlugin("LuckyOutput", func() interface{} {
		return new(LuckyOutput)
	})
}
