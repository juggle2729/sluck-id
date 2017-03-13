# -*- coding: utf-8 -*-
DEBUG = False
TEST_ENV = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['*']

QINIU_KEY_PAIR = ('sVc1BlAXhHDHYHJ7gjW4VD6iqP5zo7iC2pf9c3n8',
                  'Cixqb8jq6esZjzhHonc8OkFY3mGIIAQlOK08DCm0')
QINIU_DOMAIN = 'http://a.lucky-gou.com/'
USER_BUCKET_NAME = 'en-lucky-avatars'
ADMIN_BUCKET_NAME = 'en-lucky-pics'

TIME_OFFSET = 7
TIME_ZONE = 'Asia/Vientiane'

EXCHANGE_RATIO = 1000
REGION = u'印尼'

COUNTRY = 'id'

LANGUAGE_CODE = 'en-us'

CITY_LAN = 'id'

ROOT_URL = 'http://id.lucky-gou.com'

CELERY_BROKER = 'redis://127.0.0.1:6379//'

GEOLITE_CITY_DB = '/home/ubuntu/af-env/data/GeoLite2-City.mmdb'

LIST_UPDATE = '/home/ubuntu/af-env/luckyservice/luckycommon/virtual/list_update'

WEB_APP_ROOT_URL = 'http://id.lucky-gou.com'

ADMIN_ROOT_URL = 'http://47.88.214.2/'

INVITER_SHARE_LINK = 'http://id.lucky-gou.com/share_app2/'

XINGE_ACCESS_ID = '2200194027'
XINGE_SECRET = 'a24df2ea34f4ef67021a22a1ba41a032'
APNS_ENV = 1

# APPLE_TIDS = [647, 648, 650, 659, 660, 669, 670, 671, 672, 687, 693, 701, 702, 703, 786, 805, 808, 818]

# 禁止晒单列
# SHOW_BANNED_TIDS = [635, 636, 638, 640, 641, 642, 643, 644, 645, 646, 647, 648,
#                    649, 650, 651, 659, 654, 656, 657, 658]
SHOW_BANNED_TIDS = []

MISS_RETURN_TID = 641

# virtual goods IDs, use special strategy
VIRTUAL_GOODS_IDS = [796, 668, 667, 794, 802, 856]

COIN_TIDS = {
    #    659: 5,
    #    641: 10,
    #    642: 50,
    #    643: 100,
    #    644: 200,
    #    645: 500,
    #    646: 1000,
}

GP_FLAG = False  # GP switch, True is on sensor
GP_VERSION_CODE = 131
GP_ALLOWED_TIDS = [752, 753, 754, 755, 750, 751, 665]

IAP_FLAG = False  # IAP 审核开关
IAP_VERSION_CODE = [1, 3, 7, 8]
IAP_TEST_ID = []
IOS_DEBUG_CONF = {
    'qg_ios': 8,
}

FRESH_RECOMMEND = [0, 0]

ADMIN_ID = 1001010

CACHE_REPORT = True

JPUSH_ENV = 'prod'

MONGO_ADDR = "mongodb://10.25.164.238/"

MYSQL_CONF = {
    'db': 'mysql://lucky:P@55word@10.25.164.238:3306/lucky?charset=utf8',
    'DEBUG': DEBUG
}

SLAVE_CONF = {
    'db': 'mysql://lucky:P@55word@10.25.164.238:3306/lucky?charset=utf8',
    'DEBUG': DEBUG
}

ADMIN_CONF = {
    'db': 'mysql://lucky:P@55word@10.25.164.238:3306/admin?charset=utf8',
    'DEBUG': DEBUG
}

REDIS_HOST = '10.25.164.238'
REDIS_PORT = 6379

# Track via Rakam
RAKAM_HOST = "http://54.179.142.74:9999"
WRITE_KEY = "epbjnk945hb171m387ki71dmht30i3tq9lcjpuka0mb3h119lcpef1tslfb43fma"
MASTER_KEY = "mm7snjid3dal5kqb7in2to8ieamuo4sodel9gbiajsdkbd7jtpsl130vdm0849bu"

DEBUG_USER = 1001010
BAN_VIRTUAL_LOGIN = False

SERVICE_ID = 1

ANNOUNCE_DELAY = 300

# paypal settings
PAYPAL_REDIRECT_URL = "https://www.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=%s"
PAYPAL_API_USERNAME = "tokoseribu.id_api1.gmail.com"
PAYPAL_API_PASSWORD = "NM9R6AYQ67B4LV84"
PAYPAL_API_SIGNATURE = "AFcWxV21C7fd0v3bYYYRCpSSRl31AHfwRGYJfzLcwi-.BLrQMUf3ZxLi"
PAYPAL_API_ENVIRONMENT = 'PRODUCTION'

PAYPAL_NOTIFY_URL = 'http://121.40.29.144/api/v1/pay/paypal/notify'
PAYPAL_SUCCESS_URL = 'http://121.40.29.144/api/v1/pay/paypal/success'
PAYPAL_FAILED_URL = 'http://121.40.29.144/api/v1/pay/paypal/failed'
PAYPAL_RETURN_URL = 'http://121.40.29.144/api/v1/pay/close_webview'
PAYPAL_CANCEL_URL = 'http://121.40.29.144/api/v1/pay/close_webview'

# NganLuong pay
NGANLUONG_CHECK_ORDER_URL = 'http://id.lucky-gou.com/api/v1/pay/nganluong/check_order'
NGANLUONG_RETURN_URL = 'http://id.lucky-gou.com/api/v1/pay/nganluong/return'
NGANLUONG_NOTIFY_URL = 'http://id.lucky-gou.com/api/v1/pay/nganluong/notify'
NGANLUONG_CLOSE_URL = 'http://id.lucky-gou.com/api/v1/pay/close_webview'

# Coda pay
CODA_PAY_GATEWAY_URL = 'http://id.lucky-gou.com/api/v1/pay/coda_pay/gateway/%s/'
CODA_PAY_ORDER_URL = 'https://airtime.codapayments.com/airtime/api/restful/v1.0/Payment/init/'
CODA_PAY_CSS = 'https://airtime.codapayments.com/airtime/css/airtime_v1.0.css'
CODA_PAY_JS = 'https://airtime.codapayments.com/airtime/js/airtime_v1.0.js'
CODA_API_KEY_DICT = {
    'TWD': '66180937d31a768a62bf463b3d5e5547',
    'IDR': '3d808b4a286535ad0ad2603620232b60',
}

# Fortumo pay
FORTUMO_SERVICE_ID = '8f06a4b67822839c44bef2eebb516ac8'
FORTUMO_SECRET = 'ab19ee77832943b1631dd00331533a4b'
FORTUMO_NOTIFY_URL = 'http://id.lucky-gou.com/api/v1/pay/fortumo/notify/'
FORTUMO_CLOSE_URL = 'http://id.lucky-gou.com/api/v1/pay/close_webview/'

# Precard
PRECARD_GATEWAY_URL = 'http://id.lucky-gou.com/api/v1/pay/precard/%s/'
PAY_GATEWAY_STATUS_URL = 'http://id.lucky-gou.com/api/v1/pay/%s/status'
