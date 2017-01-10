# -*- coding: utf-8 -*-
DEBUG = False

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

MONGO_ADDR = "mongodb://127.0.0.1/"

# FIXME: NOT SAFE
CORS_ORIGIN_ALLOW_ALL = True

MYSQL_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/lucky?charset=utf8',
    'DEBUG': DEBUG
}

ADMIN_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/admin?charset=utf8',
    'DEBUG': DEBUG
}

DEBUG_USER = 1

SERVICE_ID = 1

FRESH_RECOMMEND = [129, 122]

GOD_TIDS = [129]

ANNOUNCE_DELAY = 30
