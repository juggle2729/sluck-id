package coupon

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/garyburd/redigo/redis"
	_ "github.com/go-sql-driver/mysql"
	"gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
	"sync"
	"time"

	. "github.com/mozilla-services/heka/pipeline"
)

type CouponOutput struct {
	*CouponOutputConfig
	Mg       *mgo.Session
	Rd       *redis.Pool
	Db       *sql.DB
	PackChan chan *PipelinePack
	wg       *sync.WaitGroup
	or       OutputRunner
}

type MongoExport struct {
	CouponId int
	UserId   int64
	Set      bson.M
	Data     bson.M
}

type CouponOutputConfig struct {
	MongoAddr      []string `toml:"mongo_addr"`
	RedisAddr      string   `toml:"redis_addr"`
	MySQLAddr      string   `toml:"mysql_addr"`
	ConnectTimeout uint32   `toml:"connect_timeout"`
	Procs          uint32   `toml:"procs"`
	DbName         string   `toml:"db_name"`
	TableName      string   `toml:"table_name"`
}

func (o *CouponOutput) ConfigStruct() interface{} {
	return &CouponOutputConfig{
		MongoAddr:      []string{"localhost:27017"},
		RedisAddr:      "127.0.0.1:6379",
		MySQLAddr:      "lucky:123456@tcp(127.0.0.1:3306)/lucky",
		ConnectTimeout: 3,
		Procs:          2,
		DbName:         "lucky",
		TableName:      "coupon",
	}
}

func (o *CouponOutput) Init(config interface{}) (err error) {
	o.CouponOutputConfig = config.(*CouponOutputConfig)
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
	if o.Db, err = sql.Open("mysql", o.MySQLAddr); err != nil {
		return err
	}
	if err = o.Db.Ping(); err != nil {
		return err
	}
	o.Db.SetMaxIdleConns(3)
	o.Db.SetMaxOpenConns(10)
	return nil
}

func (o *CouponOutput) Run(or OutputRunner, h PluginHelper) (err error) {
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

func save(o *CouponOutput) {
	var (
		err error
		db  *mgo.Database
	)
	defer o.Db.Close()
	for pack := range o.PackChan {
		session := o.Mg.Copy()
		db = session.DB(o.DbName)
		if err = o.Process(pack, db); err != nil {
			o.or.LogError(err)
		}
		session.Close()
		pack.Recycle(nil)
		o.or.UpdateCursor(pack.QueueCursor)
	}
	o.wg.Done()
}

func (o *CouponOutput) Process(pack *PipelinePack, db *mgo.Database) (err error) {
	var (
		data    MongoExport
		temp    interface{}
		ok      bool
		msgType string
	)
	payload := pack.Message.GetPayload()
	if err = json.Unmarshal([]byte(payload), &data); err != nil {
		return err
	}
	if data.CouponId == 0 {
		return fmt.Errorf("json unmarshal result couponid 0 for %v", payload)
	}
	if temp, ok = data.Data["type"]; ok {
		if msgType, ok = temp.(string); !ok {
			return fmt.Errorf("msg type format error")
		}
	} else {
		return fmt.Errorf("msg type not exist")
	}
	if msgType == "create_coupon" {
		var (
			coupon_type     int
			title           string
			desc            string
			condition_price sql.NullInt64
			start_ts        int
			expire_ts       int
		)
		err = o.Db.QueryRow(
			"select coupon_type, title, `desc`, condition_price, start_ts, "+
				"expire_ts from account_coupon where id=?", data.CouponId).Scan(
			&coupon_type, &title, &desc, &condition_price, &start_ts, &expire_ts)
		if err != nil {
			return err
		}
		data.Set["user_id"] = data.UserId
		data.Set["coupon_type"] = coupon_type
		data.Set["title"] = title
		data.Set["desc"] = desc
		if condition_price.Valid {
			data.Set["condition_price"] = condition_price.Int64
		} else {
			data.Set["condition_price"] = 0
		}
		data.Set["start_ts"] = start_ts
		data.Set["expire_ts"] = expire_ts
	} else if msgType == "use_coupon" {
		saveToRedis(&data, o)
	}
	err = saveToMongo(&data, o, db)
	return err
}

func saveToMongo(data *MongoExport, o *CouponOutput, db *mgo.Database) error {
	insertData := make(map[string]bson.M)
	if len(data.Set) > 0 {
		insertData["$set"] = data.Set
	}
	_, err := db.C(o.TableName).UpsertId(data.CouponId, insertData)
	if err != nil {
		if mgo.IsDup(err) {
			_, err = db.C(o.TableName).UpsertId(data.CouponId, insertData)
		}
		if err != nil {
			o.or.LogError(err)
		}
	}
	return err
}

func saveToRedis(data *MongoExport, o *CouponOutput) (err error) {
	var (
		temp interface{}
		ok   bool
	)
	rd := o.Rd.Get()
	key := fmt.Sprintf("stats:user:%d", data.UserId)
	if temp, ok = data.Set["price"]; ok {
		temp, err = rd.Do("HINCRBY", key, "used_coupon", temp)
	}
	return
}

func init() {
	RegisterPlugin("CouponOutput", func() interface{} {
		return new(CouponOutput)
	})
}
