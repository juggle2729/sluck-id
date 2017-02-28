# -*- coding: utf-8 -*-
# default settings, use as test env settings
# production settings should be settings_online, see `deploy/online/deploy.json` - `bash` section
DEBUG = True
TEST_ENV = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']

QINIU_KEY_PAIR = ('sVc1BlAXhHDHYHJ7gjW4VD6iqP5zo7iC2pf9c3n8',
                  'Cixqb8jq6esZjzhHonc8OkFY3mGIIAQlOK08DCm0')
QINIU_DOMAIN = 'http://oi9q1c7wq.bkt.clouddn.com/'
USER_BUCKET_NAME = 'lucky-test'
ADMIN_BUCKET_NAME = 'lucky-test'

TIME_OFFSET = 7
TIME_ZONE = 'Asia/Vientiane'

EXCHANGE_RATIO = 1000
REGION = u'印尼'

COUNTRY = 'id'

LANGUAGE_CODE = 'en-us'

CITY_LAN = 'id'

ROOT_URL = 'http://121.40.29.144/'

CELERY_BROKER = 'redis://127.0.0.1:6379//'

GEOLITE_CITY_DB = '/home/ubuntu/af-env/data/GeoLite2-City.mmdb'

LIST_UPDATE = '/home/ubuntu/af-env/luckyservice/luckycommon/virtual/list_update'

WEB_APP_ROOT_URL = 'http://121.40.29.144:9898'

ADMIN_ROOT_URL = 'http://121.40.29.144/'

INVITER_SHARE_LINK = 'http://121.40.29.144/share_app2/'

IOS_DEBUG_CONF = {
    'qg_ios': 1,
    # 'int_ios_us': 6,
    # 'int_ios_tw': 6,
    # 'int_ios_uk': 9,
}

XINGE_ACCESS_ID = '2200194027'
XINGE_SECRET = 'a24df2ea34f4ef67021a22a1ba41a032'
APNS_ENV = 1

APPLE_TIDS = [647, 648, 650, 659, 660, 669, 670, 671, 672, 687, 693, 701, 702, 703, 786, 805, 808, 818]

# 禁止晒单列
# SHOW_BANNED_TIDS = [635, 636, 638, 640, 641, 642, 643, 644, 645, 646, 647, 648,
#                    649, 650, 651, 659, 654, 656, 657, 658]
SHOW_BANNED_TIDS = []

MISS_RETURN_TID = 641

COIN_TIDS = {
    #    659: 5,
    #    641: 10,
    #    642: 50,
    #    643: 100,
    #    644: 200,
    #    645: 500,
    #    646: 1000,
}

GP_FLAG = False  # GP sensor switch, True is on
GP_VERSION_CODE = 128
GP_ALLOWED_TIDS = [752, 753, 754, 755, 750, 751, 665]

IAP_FLAG = True  # IAP 审核开关
IAP_VERSION_CODE = [1, ]
IAP_TEST_ID = [298, 18045996]


FRESH_RECOMMEND = [0, 0]

ADMIN_ID = 1001010

CACHE_REPORT = True

JPUSH_ENV = 'prod'

MONGO_ADDR = "mongodb://127.0.0.1/"

MYSQL_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/lucky?charset=utf8',
    'DEBUG': False
}

SLAVE_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/lucky?charset=utf8',
    'DEBUG': False
}

ADMIN_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/admin?charset=utf8',
    'DEBUG': False
}

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

DEBUG_USER = 1001010
BAN_VIRTUAL_LOGIN = False

SERVICE_ID = 1

ANNOUNCE_DELAY = 30

# paypal settings
PAYPAL_REDIRECT_URL = "https://www.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=%s"
PAYPAL_API_USERNAME = "sunshineking86_api1.gmail.com"
PAYPAL_API_PASSWORD = "E869TNPC95U2Z4JC"
PAYPAL_API_SIGNATURE = "AFcWxV21C7fd0v3bYYYRCpSSRl31Aq0XfM5N.PRkiDU4yeS-Fbj7jo0X"
PAYPAL_API_ENVIRONMENT = 'PRODUCTION'

PAYPAL_NOTIFY_URL = 'http://121.40.29.144/api/v1/pay/paypal/notify'
PAYPAL_SUCCESS_URL = 'http://121.40.29.144/api/v1/pay/paypal/success'
PAYPAL_FAILED_URL = 'http://121.40.29.144/api/v1/pay/paypal/failed'
PAYPAL_RETURN_URL = 'http://121.40.29.144/api/v1/pay/close_webview'
PAYPAL_CANCEL_URL = 'http://121.40.29.144/api/v1/pay/close_webview'

# NganLuong pay
NGANLUONG_CHECK_ORDER_URL = 'http://121.40.29.144/api/v1/pay/nganluong/check_order'
NGANLUONG_RETURN_URL = 'http://121.40.29.144/api/v1/pay/nganluong/return'
NGANLUONG_NOTIFY_URL = 'http://121.40.29.144/api/v1/pay/nganluong/notify'
NGANLUONG_CLOSE_URL = 'http://121.40.29.144/api/v1/pay/close_webview'

# Coda pay
CODA_PAY_GATEWAY_URL = 'http://121.40.29.144/api/v1/pay/coda_pay/gateway/%s/'
CODA_PAY_ORDER_URL = 'https://sandbox.codapayments.com/airtime/api/restful/v1.0/Payment/init/'
CODA_API_KEY_DICT = {
    'TWD': '66180937d31a768a62bf463b3d5e5547',
    'IDR': '3d808b4a286535ad0ad2603620232b60',
}

# Fortumo pay
FORTUMO_SERVICE_ID = '8f06a4b67822839c44bef2eebb516ac8'
FORTUMO_SECRET = 'ab19ee77832943b1631dd00331533a4b'
FORTUMO_NOTIFY_URL = 'http://121.40.29.144/api/v1/pay/fortumo/notify/'
FORTUMO_CLOSE_URL = 'http://121.40.29.144/api/v1/pay/close_webview/'

# Precard
PRECARD_GATEWAY_URL = 'http://121.40.29.144/api/v1/pay/precard/%s/'
PAY_GATEWAY_STATUS_URL = 'http://121.40.29.144/api/v1/pay/%s/status'
