# -*- coding: utf-8 -*-
DEBUG = False

TEST_ENV = False

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ORIGIN_REGEX_WHITELIST = ('^(https?://)?(\w+\.)?1yuan-gou\.com$', )

QINIU_KEY_PAIR = ('sVc1BlAXhHDHYHJ7gjW4VD6iqP5zo7iC2pf9c3n8',
                  'Cixqb8jq6esZjzhHonc8OkFY3mGIIAQlOK08DCm0')
QINIU_DOMAIN = 'http://avatar.1yuan-gou.com/'

USER_BUCKET_NAME = 'lucky-avatars'
ADMIN_BUCKET_NAME = 'lucky-pics'

COUNTRY = 'cn'

ROOT_URL = 'http://120.27.162.212'

CELERY_BROKER = 'redis://127.0.0.1:6379//'

GEOLITE_CITY_DB = '/home/ubuntu/af-env/data/GeoLite2-City.mmdb'

LIST_UPDATE = '/home/ubuntu/af-env/luckyservice/luckycommon/virtual/list_update'

WEB_APP_ROOT_URL = 'http://www.1yuan-gou.com'

ADMIN_ROOT_URL = 'http://120.26.57.89/'

INVITER_SHARE_LINK = 'http://www.1yuan-gou.com/share_app2/'

IOS_DEBUG_CONF = {
    'ios': 29,
    'ios_pro': 29,
    'ios_hd': 29,
    'qg_ios': 26,
    'qg_pro': 1,
    'qg_hd': 1,
}

XINGE_ACCESS_ID = '2200194027'
XINGE_SECRET = 'a24df2ea34f4ef67021a22a1ba41a032'
APNS_ENV = 1

APPLE_TIDS = [235, 120, 121, 122, 206, 124, 125, 221, 123, 563, 568, 543, 580, 581, 583,
              553, 587, 185, 282, 306, 308, 328, 354, 340, 360, 372, 427, 428, 430, 582, 612, 638]

SHOW_BANNED_TIDS = [397, 398, 424, 425, 426, 483, 485, 486, 488, 588,
                    331, 421, 460, 461, 462, 463, 506, 519, 520, 521, 597,
                    522, 523, 524, 525, 526, 527, 528, 529, 530, 531]

COIN_TIDS = {
    397: 10,
    398: 100,
    424: 200,
    425: 500,
    426: 1000,
    483: 200,
    485: 100,
    486: 500,
    488: 300,
    588: 200,
}

CARD_TIDS = [460, 461, 462, 463, 506, 522, 523, 524, 597,
             525, 526, 527, 528, 529, 530, 531, 519, 520, 521]

RED_ENVELOPE_TIDS = {
    # template_id : price
    506: 10,
    460: 30,
    461: 50,
    462: 100,
    463: 200,
    597: 200
}

TRANSFER_TIDS = {
}


CAMEN_TIDS = {
    # template_id : price
    # 移动
    522: {'product_id': 1138217, 'count': 1},  # 移动30
    523: {'product_id': 1138223, 'count': 1},  # 移动50
    524: {'product_id': 1138224, 'count': 1},  # 移动100
    525: {'product_id': 1138224, 'count': 2},  # 移动200
    526: {'product_id': 1138224, 'count': 5},  # 移动500
    # 联通
    527: {'product_id': 1138228, 'count': 1},  # 联通30
    528: {'product_id': 1138229, 'count': 1},  # 联通50
    529: {'product_id': 1138230, 'count': 1},  # 联通100
    530: {'product_id': 1138230, 'count': 2},  # 联通200
    531: {'product_id': 1138230, 'count': 5},  # 联通500
    # 电信
    519: {'product_id': 1138266, 'count': 1},  # 电信100
    520: {'product_id': 1138266, 'count': 2},  # 电信200
    521: {'product_id': 1138266, 'count': 5},  # 电信500
}

# weixin settings
WX_APP_ID = "wx3bded55c34db1844"
WX_SECRET_KEY = "e5bf72f5961bb4412e0176c912bca8ae"
WX_CLIENT_TOKEN = "zYmnWmXGsbDhgVttvfpH272WCfTz5gUH"
WX_ENCODING_AES_KEY = "J4fzqiBDtba6hLT1xvbfvxRND5AT6TGOiWp0AHqpHOx"

ADMIN_ID = 1001010

CACHE_REPORT = True

MONGO_ADDR = "mongodb://10.168.5.23/"

MYSQL_CONF = {
    'db': 'mysql://lucky:P@55word@10.25.235.79:3306/lucky?charset=utf8',
    'DEBUG': DEBUG
}

SLAVE_CONF = {
    'db': 'mysql://lucky:P@55word@10.25.242.204:3306/lucky?charset=utf8',
    'DEBUG': DEBUG
}

ADMIN_CONF = {
    'db': 'mysql://lucky:P@55word@10.25.235.79:3306/admin?charset=utf8',
    'DEBUG': DEBUG
}

ENABLE_CODIS = True

REDIS_HOST = '10.46.71.31'
REDIS_PORT = 6479

ZK_HOSTS = '10.46.71.31:2181'
ZK_PROXY_DIR = '/zk/codis/db_test/proxy'

DEBUG_USER = 1001010
BAN_VIRTUAL_LOGIN = False

SERVICE_ID = 1

# PingPlusPlus config

# Pingpp App key
APP_ID = 'app_TOabLOTi58C0T4av'

# Pingpp alipay wap return and cancel URL
SUCCESS_URL = 'http://www.yourdomain.com/success'
CANCEL_URL = 'http://www.yourdomain.com/cancel'

# iapppay notify URL
IAPPPAY_NOTIFY_URL = 'http://120.27.162.212/api/v1/pay/iapppay/notify/'

# iapppay tmp notify URL
IAPPPAY_TMP_NOTIFY_URL = 'http://120.27.162.212/api/v1/pay/iapppay_tmp/notify/'

# ipaynow notify URL
IPAYNOW_NOTIFY_URL = 'http://120.27.162.212/api/v1/pay/ipaynow/notify/'

# ofpay notify url
OFFPAY_NOTIFY_URL = 'http://120.27.162.212/api/v1/ofpay/'

# swiftpass notify url
SWIFTPASS_NOTIFY_URL = 'http://120.27.162.212/api/v1/swiftpass/'

# shenfutong notify url
SHENFUTONG_NOTIFY_URL = 'http://120.27.162.212/api/v1/shenfutong/notify/'
SHENFUTONG_RETURN_URL = 'http://120.27.162.212/api/v1/shenfutong/return/'

# gaoyang notify url
GAOYANG_NOTIFY_URL = 'http://120.27.162.212/api/v1/pay/gaoyang/notify/'
PAY_GATEWAY_URL = 'http://120.27.162.212/api/v1/pay/gateway/'
PAY_GATEWAY_STATUS_URL = 'http://120.27.162.212/api/v1/pay/%s/status'

# paypayfu notify url
PAYPAYFU_NOTIFY_URL = 'http://120.27.162.212/api/v1/pay/paypayfu/notify/'

# mingtianyun notify url
MINGTIANYUN_NOTIFY_URL = 'http://120.27.162.212/api/v1/pay/mingtianyun/notify/'

FRESH_RECOMMEND = [568, 331]
