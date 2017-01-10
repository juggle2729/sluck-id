# -*- coding: utf-8 -*-
DEBUG = False

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ORIGIN_ALLOW_ALL = True

COUNTRY = 'cn'

ROOT_URL = 'http://121.41.6.238'

CELERY_BROKER = 'redis://127.0.0.1:6379//'

GEOLITE_CITY_DB = '/home/ubuntu/af-env/data/GeoLite2-City.mmdb'

LIST_UPDATE = '/home/ubuntu/af-env/luckyservice/tools/data/online_test/list_update1'

WEB_APP_ROOT_URL = 'http://121.41.6.238:9898'

ADMIN_ROOT_URL = 'http://121.41.6.238/'

INVITER_SHARE_LINK = 'http://121.41.6.238:9898/share_app/'

APPLE_TIDS = [123, 117, 138, 118, 121, 122, 124, 125]

MONGO_ADDR = "mongodb://127.0.0.1/"

MYSQL_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/lucky?charset=utf8',
    'DEBUG': DEBUG
}

ADMIN_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/admin?charset=utf8',
    'DEBUG': DEBUG
}

ENABLE_CODIS = False

ZK_HOSTS = '172.31.1.71:2181,172.31.1.99:2182,172.31.1.99:2183,172.31.1.71:2184,172.31.1.71:2185'
ZK_PROXY_DIR = '/zk/codis/db_test/proxy'

DEBUG_USER = 1

SERVICE_ID = 1

FRESH_RECOMMEND = [129, 122]

GOD_TIDS = [129]

SPRING_GROUP = [{
    'gid': 125, 'cover': 'http://p.1yuan-gou.com/o_1ac9184n519mar0ee5kdi91iki9.jpg', 'title': u'百草味饼干蛋糕',
},{
    'gid': 129, 'cover': 'http://p.1yuan-gou.com/o_1afne0sth1f923qomus6cp137e9.jpg', 'title': u'锐澳鸡尾酒',
},{
    'gid': 133, 'cover': 'http://p.1yuan-gou.com/o_1abf9n8q4ga368v14df1jnduij9.jpg', 'title': u'李锦记XO酱',
},{
    'gid': 143, 'cover': 'http://p.1yuan-gou.com/o_1agtuq8rt1k8e1rtm1h4mei076k9.jpg', 'title': u'自游人睡垫',
},{
    'gid': 125, 'cover': 'http://p.1yuan-gou.com/o_1ac90n3ipbca1k4n1pl43oiu9b9.jpg', 'title': u'红色营地帐篷',
},{
    'gid': 129, 'cover': 'http://p.1yuan-gou.com/o_1af8fvbtndjjh7p911lat1o2p9.jpg', 'title': u'尚烤佳户外烧烤炉',
},{
    'gid': 133, 'cover': 'http://p.1yuan-gou.com/o_1aao3s2ka4s11td6kfh6cc14os9.jpg', 'title': u'埃尔蒙特旅行洗漱包',
},{
    'gid': 143, 'cover': 'http://p.1yuan-gou.com/o_1adafemqg1qdh1p7onmv176f138k9.jpg', 'title': u'乐扣乐扣便当盒',
},{
    'gid': 125, 'cover': 'http://p.1yuan-gou.com/o_1aao3tho41c5s7496op1ar51dmu9.jpg', 'title': u'爱华仕拉杆箱',
},{
    'gid': 129, 'cover': 'http://p.1yuan-gou.com/o_1aao43vggureio5cqd1a123cb9.jpg', 'title': u'东菱早餐机',
},{
    'gid': 133, 'cover': 'http://p.1yuan-gou.com/o_1af7tb7ct1e3qnnm1dlr1kb1nr4l.jpg', 'title': u'大疆精灵无人机',
},{
    'gid': 143, 'cover': 'http://p.1yuan-gou.com/o_1afqatgn411dt1ia2rg31hpk85rl.jpg', 'title': u'苹果SE16G',
}]

ANNOUNCE_DELAY = 30
