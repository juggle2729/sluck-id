# -*- coding: utf-8 -*-
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']

COUNTRY = 'vn'

CITY_LAN = 'vn'

LANGUAGE_CODE = 'en-us'

ROOT_URL = 'http://121.40.29.144'

CELERY_BROKER = 'redis://127.0.0.1:6379//'

GEOLITE_CITY_DB = '/home/ubuntu/af-env/data/GeoLite2-City.mmdb'

LIST_UPDATE = '/home/ubuntu/af-env/luckyservice/tools/data/online_test/list_update1'

WEB_APP_ROOT_URL = 'http://121.40.29.144:9898'

ADMIN_ROOT_URL = 'http://121.40.29.144/'

INVITER_SHARE_LINK = 'http://121.40.29.144:9898/share_app/'

APPLE_TIDS = [123, 117, 138, 118, 121, 122, 124, 125]

RAVEN_CONFIG = {
    'dsn': 'http://eb86dcf4383342e986a991ba3df94341:ef5ea26ffd054f2e8ea9f5887ab6cdde@114.55.27.19:9000/3',
}

MONGO_ADDR = "mongodb://127.0.0.1/"

# FIXME: NOT SAFE
CORS_ORIGIN_ALLOW_ALL = True

MYSQL_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/lucky?charset=utf8',
    'DEBUG': False
}

ADMIN_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/admin?charset=utf8',
    'DEBUG': False
}

DEBUG_USER = 1

SERVICE_ID = 1

FRESH_RECOMMEND = [129, 122]

GOD_TIDS = [129]

ANNOUNCE_DELAY = 30

# paypal settings
PAYPAL_REDIRECT_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=%s"
PAYPAL_API_USERNAME = "sunshineking86-facilitator_api1.gmail.com"
PAYPAL_API_PASSWORD = "WR4ZHKZNWHPSR65D"
PAYPAL_API_SIGNATURE = "AFcWxV21C7fd0v3bYYYRCpSSRl31AbDl8KV.UJSCOn1uuHTE0e1Vs3R0"
PAYPAL_API_ENVIRONMENT = 'SANDBOX'

PAYPAL_RETURN_URL = 'http://121.40.29.144/api/v1/pay/paypal/return'
PAYPAL_CANCEL_URL = 'http://121.40.29.144/api/v1/pay/paypal/cancel'
PAYPAL_NOTIFY_URL = 'http://121.40.29.144/api/v1/pay/paypal/notify'

# NganLuong pay
NGANLUONG_CHECK_ORDER_URL = 'http://121.40.29.144/api/v1/pay/nganluong/check_order'
NGANLUONG_RETURN_URL = 'http://121.40.29.144/api/v1/pay/nganluong/return'
NGANLUONG_NOTIFY_URL = 'http://121.40.29.144/api/v1/pay/nganluong/notify'
NGANLUONG_CLOSE_URL = 'http://121.40.29.144/api/v1/pay/close_webview'

# Coda pay
CODA_PAY_GATEWAY_URL = 'http://121.40.29.144/api/v1/pay/coda_pay/gateway/%s/'
CODA_API_KEY_DICT = {
    'TWD': '66180937d31a768a62bf463b3d5e5547',
    'IDR': 'f0e5a52f4171b6d4d6b1a1b5b77b3ad0',
}

# Fortumo pay
FORTUMO_SERVICE_ID = '964f5dc6556ef062e2d6883ef94908e6'
FORTUMO_SECRET = 'efd5746d7a21224c6e9fa95beb9c95bf'
FORTUMO_NOTIFY_URL = 'http://121.40.29.144/api/v1/pay/fortumo/notify/'
FORTUMO_CLOSE_URL = 'http://121.40.29.144/api/v1/pay/close_webview/'

# Precard
PRECARD_GATEWAY_URL = 'http://121.40.29.144/api/v1/pay/precard/%s/'
PAY_GATEWAY_STATUS_URL = 'http://121.40.29.144/api/v1/pay/%s/status'
