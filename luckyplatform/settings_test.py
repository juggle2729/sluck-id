# -*- coding: utf-8 -*-
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ROOT_URL = 'http://121.41.6.238:8000'

CELERY_BROKER = 'redis://127.0.0.1:6379//'

MYSQL_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/lucky?charset=utf8',
    'DEBUG': DEBUG
}

ADMIN_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/admin?charset=utf8',
    'DEBUG': DEBUG
}

ZK_HOSTS = '172.31.1.71:2181,172.31.1.99:2182,172.31.1.99:2183,172.31.1.71:2184,172.31.1.71:2185'

ZK_PROXY_DIR = '/zk/codis/db_test/proxy'

DEBUG_USER = 1

SERVICE_ID = 1

# PingPlusPlus config

# Pingpp App key
API_KEY = 'sk_live_KuPGuHmDuvr5qTyrbDaz180G'

# Pingpp alipay wap return and cancel URL
SUCCESS_URL = 'http://www.yourdomain.com/success'
CANCEL_URL = 'http://www.yourdomain.com/cancel'

# iapppay notify URL
IAPPPAY_NOTIFY_URL = 'http://121.41.6.238/api/v1/pay/iapppay/notify/'

# ipaynow notify URL
IPAYNOW_NOTIFY_URL = 'http://121.41.6.238/api/v1/pay/ipaynow/notify/'

FRESH_RECOMMEND = [129, 122]

GOD_TIDS = [129]

SPRING_GROUP = [{
    'gid': 125, 'cover': '', 'title': '',
},{
    'gid': 129, 'cover': '', 'title': '',
},{
    'gid': 133, 'cover': '', 'title': '',
},{
    'gid': 143, 'cover': '', 'title': '',
}]

ANNOUNCE_DELAY = 30
