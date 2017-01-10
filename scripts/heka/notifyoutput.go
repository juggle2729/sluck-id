package lucky

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/garyburd/redigo/redis"
	"gopkg.in/gomail.v2"
	"net/http"
	"net/url"
	"reflect"
	"sync"
	"time"

	. "github.com/mozilla-services/heka/pipeline"
)

const (
	URL     = "https://api.submail.cn/message/multixsend.json"
	APPID   = "10685"
	APP_KEY = "8419e355ac064269f34e5c34d652f082"

	MAIL_ADDR        = "ops@adsquare-tech.com"
	MAIL_HOST        = "smtp.mxhichina.com"
	MAIL_PORT        = 25
	MAIL_PASSWD      = "madP@ssw0rd"
	MAIL_FROM        = "OPS Platform<ops@adsquare-tech.com>"
	R_TEMPLATE       = "sxaM9"
	BIG_HIT_TEMPLATE = "XzH57"
)

type NotifyOutput struct {
	*NotifyOutputConfig
	Rd       *redis.Pool
	PackChan chan *PipelinePack
	wg       *sync.WaitGroup
	or       OutputRunner
}

type NotifyOutputConfig struct {
	PhoneNums    []string `toml:"phone_nums"`
	Emails       []string `tomal:"emails"`
	RedisAddr    string   `toml:"redis_addr"`
	Expire       int      `toml:"expire"`
	Procs        uint32   `toml:"procs"`
	SumThreshold []uint32 `toml:"sum_threshold"`
	WinThreshold uint32   `toml:"win_threshold"`
}

func (o *NotifyOutput) ConfigStruct() interface{} {
	return &NotifyOutputConfig{
		PhoneNums:    []string{},
		Emails:       []string{},
		RedisAddr:    "127.0.0.1:6379",
		Expire:       6 * 3600,
		Procs:        5,
		SumThreshold: []uint32{500, 1000, 2000, 5000, 10000},
		WinThreshold: 2000,
	}
}

func (o *NotifyOutput) Init(config interface{}) (err error) {
	o.NotifyOutputConfig = config.(*NotifyOutputConfig)
	o.PackChan = make(chan *PipelinePack, int(o.Procs))
	if len(o.PhoneNums) == 0 && len(o.Emails) == 0 {
		return errors.New("config at least one phone num or one email")
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

func (o *NotifyOutput) Run(or OutputRunner, h PluginHelper) (err error) {
	o.or = or
	o.wg = new(sync.WaitGroup)

	for i := 0; i < int(o.Procs); i++ {
		o.wg.Add(1)
		go notify(o)
	}
	for pack := range or.InChan() {
		o.PackChan <- pack
	}
	close(o.PackChan)
	o.wg.Wait()
	return nil
}

func notify(o *NotifyOutput) {
	var (
		err error
	)
	for pack := range o.PackChan {
		if err = o.Process(pack); err != nil {
			o.or.LogError(err)
			pack.Recycle(err)
		} else {
			pack.Recycle(nil)
		}
		o.or.UpdateCursor(pack.QueueCursor)
	}
	o.wg.Done()
}

func (o *NotifyOutput) sendSMS(vars *map[string]interface{}, templateId string) error {
	multi := make([]map[string]interface{}, len(o.PhoneNums), len(o.PhoneNums))
	for index, phone := range o.PhoneNums {
		content := make(map[string]interface{})
		content["to"] = phone
		content["vars"] = *vars
		multi[index] = content
	}
	multiStr, err := json.Marshal(multi)
	if err != nil {
		return err
	}
	_, err = http.PostForm(URL, url.Values{"appid": {APPID}, "project": {templateId},
		"multi": {string(multiStr)}, "signature": {APP_KEY}})
	if err != nil {
		o.or.LogError(err)
		return err
	}
	return nil
}

func (o *NotifyOutput) sendEmail(title string, body string) error {
	m := gomail.NewMessage()
	m.SetHeader("From", MAIL_FROM)
	m.SetHeader("To", o.Emails...)
	m.SetHeader("Subject", title)
	m.SetBody("text/html", body)

	d := gomail.NewPlainDialer(MAIL_HOST, MAIL_PORT, MAIL_ADDR, MAIL_PASSWD)
	if err := d.DialAndSend(m); err != nil {
		o.or.LogError(err)
		return err
	}
	return nil
}

func (o *NotifyOutput) processRecharge(amount int, userId int64) {
	var (
		emailContent string
		needNotify   bool
	)
	smsVars := make(map[string]interface{})
	rd := o.Rd.Get()
	key := fmt.Sprintf("notify:recharge:%d", userId)
	recharged, err := redis.Int(rd.Do("GET", key))
	if err != nil && err != redis.ErrNil {
		fmt.Println("can't read from redis!!!!!!!!!!!")
		return
	}
	after_recharge := recharged + amount
	for _, value := range o.SumThreshold {
		if recharged < int(value) && after_recharge >= int(value) {
			needNotify = true
			break
		}
	}
	if needNotify {
		smsVars["user_id"] = fmt.Sprintf("%d累计", userId)
		smsVars["recharge"] = after_recharge
		emailContent = fmt.Sprintf("用户%d累计充值已达%d元，请留意！", userId, after_recharge)
	}
	rd.Do("INCRBY", key, amount)
	rd.Do("EXPIRE", key, o.Expire)
	if needNotify {
		o.sendSMS(&smsVars, R_TEMPLATE)
		o.sendEmail("【线上通知】土豪出现了！", emailContent)
	}
}

func (o *NotifyOutput) processWin(data map[string]interface{}, userId int64, target int) {
	smsVars := make(map[string]interface{})
	smsVars["user_id"] = userId
	smsVars["target"] = target
	smsVars["term"] = data["term_number"]
	smsVars["name"] = data["activity_name"]
	o.sendSMS(&smsVars, BIG_HIT_TEMPLATE)
}

func convertToInt(temp interface{}) (int, error) {
	switch t := temp.(type) {
	case int:
		return int(t), nil
	case float64, float32:
		return int(reflect.ValueOf(t).Float()), nil
	case int64, int32:
		return int(reflect.ValueOf(t).Int()), nil
	default:
		return 0, errors.New("format wrong")
	}
}

func (o *NotifyOutput) Process(pack *PipelinePack) (err error) {
	var (
		data    MongoExport
		ok      bool
		temp    interface{}
		msgType string
	)
	payload := pack.Message.GetPayload()
	if err = json.Unmarshal([]byte(payload), &data); err != nil {
		return err
	}
	if data.UserId == 0 {
		return fmt.Errorf("json unmarshal result userid 0 for %v", payload)
	}
	msgType = pack.Message.GetType()
	if msgType == "recharge" {
		var toRecharge int
		if temp, ok = data.Inc["recharge.total"]; !ok {
			return errors.New("no recharge at all")
		}
		if toRecharge, err = convertToInt(temp); err != nil {
			return err
		}
		o.processRecharge(toRecharge, data.UserId)
	} else if msgType == "win" {
		var target int
		if temp, ok = data.Data["activity_target"]; !ok {
			return errors.New("no activity target field")
		}
		if target, err = convertToInt(temp); err != nil {
			return err
		}
		if target < int(o.WinThreshold) {
			return nil
		}
		if ok, _ := IsVirtual(data.UserId, o.Rd); ok {
			return nil
		}
		o.processWin(data.Data, data.UserId, target)
	}
	return
}

func init() {
	RegisterPlugin("NotifyOutput", func() interface{} {
		return new(NotifyOutput)
	})
}
