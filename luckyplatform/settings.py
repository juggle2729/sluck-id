# -*- coding: utf-8 -*-
import os
import raven

from luckyplatform.jsonlogger import JsonFormatter

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = 'mzm2ojrfc54x#9%dptxc4c-!pa3ppj!h(5=@^h*346k-fs65vi'

DEBUG = True

TEST_ENV = False

TEMPLATE_DEBUG = True

CACHE_REPORT = False

ALLOWED_HOSTS = ['*']

QINIU_KEY_PAIR = ('sVc1BlAXhHDHYHJ7gjW4VD6iqP5zo7iC2pf9c3n8',
                  'Cixqb8jq6esZjzhHonc8OkFY3mGIIAQlOK08DCm0')
QINIU_DOMAIN = 'http://oi9q1c7wq.bkt.clouddn.com/'
USER_BUCKET_NAME = 'lucky-test'
ADMIN_BUCKET_NAME = 'lucky-test'

REGION = u'测试'

COUNTRY = 'id'

CITY_LAN = 'id'

ROOT_URL = 'http://192.168.0.220:8000'

CELERY_BROKER = 'redis://192.168.0.220:6379//'

MONGO_ADDR = "mongodb://127.0.0.1/"

GEOLITE_CITY_DB = '/home/ubuntu/af-env/data/GeoLite2-City.mmdb'

LIST_UPDATE = '/home/ubuntu/af-env/luckyservice/luckycommon/virtual/list_update'

WEB_APP_ROOT_URL = 'http://121.40.29.144:9898'

ADMIN_ROOT_URL = 'http://120.26.57.89/'

INVITER_SHARE_LINK = 'http://vn.lucky-gou.com/share_app/'

IOS_DEBUG_CONF = {
    'ios': 1,
    'ios_pro': 1,
    'qg_ios': 1,
}

FRESH_RECOMMEND = [129, 122]

HUAFEI_TIDS = [331, 332, 333, 334, 129, 130,
               335, 382, 383, 384, 385, 421, 422, 423, 398, 425, 426, 424]

APPLE_TIDS = [235, 120, 121, 122, 206, 124, 125, 221, 123, 185, 282]

CARD_TIDS = [460, 461, 462, 463]

HOT_TIDS = [330, 361, 302, 348, 353, 357, 340, 386]

GOD_TIDS = [129, 331, 332, 333, 334]

# 禁止晒单列
# SHOW_BANNED_TIDS = [635, 657, 672, 659, 651, 649, 647, ]

COIN_TIDS = {
    659: 5,
    641: 10,
    642: 50,
    643: 100,
    644: 200,
    645: 500,
    646: 1000,
}

MISS_RETURN_TID = 641

ADV_FLAG = False  # GP版开关, 旧版不用放着

GP_FLAG = False  # GP switch, True is on sensor
GP_VERSION_CODE = 130
GP_ALLOWED_TIDS = [752, 753, 754, 755, 662, 664, 663, 665]

ADMIN_ID = 1

XINGE_IOS_ACCESS_ID = '2200194027'
XINGE_IOS_SECRET = 'a24df2ea34f4ef67021a22a1ba41a032'
XINGE_IPAD_ACCESS_ID = '2200195666'
XINGE_IPAD_SECRET = '9718c07c9560eda89788f7afc61cdcf5'
APNS_ENV = 2
XINGE_ANDROID_ACCESS_ID = '2100194500'
XINGE_ANDROID_SECRET = '206544336be221462d78919119b4d733'

JPUSH_ENV = 'test'

EXPORT_PATH = '/tmp/export_data/'

SESSION_ENGINE = 'luckycommon.utils.session'
SESSION_COOKIE_AGE = 20 * 60

# Application definition
INSTALLED_APPS = (
    'luckyapi',
    'luckyadmin',
    'raven.contrib.django.raven_compat',
    # 'corsheaders',
    # 'luckytest'
)

RAVEN_CONFIG = {
    'dsn': 'http://3b974441d614479f88f0318a428d3f3c:8e3052d2eaea4b88b5a8e1a4a78f54ce@114.55.27.19:9000/2',
}

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'luckyplatform.middleware.UserMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

ROOT_URLCONF = 'luckyplatform.urls'

WSGI_APPLICATION = 'luckyplatform.wsgi.application'

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'templates'),
)

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

LANGUAGES = (
    ('en', ('English')),
    ('zh-cn', (u'中文简体')),
    ('zh-tw', (u'中文繁體')),
)

LOCALE_PATHS = ['/home/ubuntu/af-env/luckyservice/locale']

TIME_ZONE = 'Asia/Vientiane'

TIME_OFFSET = 7

USE_I18N = True

USE_L10N = True

USE_TZ = True

APPEND_SLASH = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

MYSQL_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/lucky?charset=utf8',
    'DEBUG': False
}

SLAVE_CONF = MYSQL_CONF

ADMIN_CONF = {
    'db': 'mysql://root:123456@127.0.0.1:3306/admin?charset=utf8',
    'DEBUG': False
}

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

DEBUG_USER = 1554499156372881408
BAN_VIRTUAL_LOGIN = False

SERVICE_ID = 1

ANNOUNCE_DELAY = 30

# exchange ratio

EXCHANGE_RATIO = 1000

# LOG CONFIG
LOG_DIR = "/var/log/lucky/"
LOG_FILE = os.path.join(LOG_DIR, "lucky.log")
LOG_ERR_FILE = os.path.join(LOG_DIR, "lucky.err.log")
WORKER_LOG_FILE = os.path.join(LOG_DIR, "worker.log")
WORKER_LOG_ERR_FILE = os.path.join(LOG_DIR, "worker.err.log")
PAY_LOG_FILE = os.path.join(LOG_DIR, "pay.log")
PAY_LOG_ERR_FILE = os.path.join(LOG_DIR, "pay.err.log")
TRACK_LOG = os.path.join(LOG_DIR, 'track.json')

try:
    from luckyplatform.env_settings import *
except ImportError:
    import logging

    logging.warn('no env specified settings loaded, use default.')
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json_stat': {
            '()': JsonFormatter,
            'format': '%(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'detail': {
            'format': '%(levelname)s %(asctime)s [%(module)s.%(funcName)s line:%(lineno)d] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'formatter': 'simple',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOG_FILE,
        },
        'pay_file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'formatter': 'simple',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': PAY_LOG_FILE,
        },
        'worker_file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'formatter': 'simple',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': WORKER_LOG_FILE,
        },
        'err_file': {
            'level': 'WARN',
            'formatter': 'detail',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOG_ERR_FILE,
        },
        'worker_err_file': {
            'level': 'WARN',
            'formatter': 'detail',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': WORKER_LOG_ERR_FILE,
        },
        'pay_err_file': {
            'level': 'WARN',
            'formatter': 'detail',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': PAY_LOG_ERR_FILE,
        },
        'track_file': {
            'level': 'INFO',
            'formatter': 'json_stat',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': TRACK_LOG
        }
    },
    'loggers': {
        'lucky': {
            'handlers': ['console', 'file', 'err_file'] if DEBUG else ['file', 'err_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'worker': {
            'handlers': ['console', 'file', 'err_file'] if DEBUG else ['worker_file', 'worker_err_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'timer': {
            'handlers': ['console', 'file', 'err_file'] if DEBUG else ['worker_file', 'worker_err_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'pay': {
            'handlers': ['console', 'pay_file', 'pay_err_file'] if DEBUG else ['pay_file', 'pay_err_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'tracker': {
            'handlers': ['track_file'],
            'level': 'INFO',
            'propagate': False
        },
        'dicttoxml': {
            'handlers': ['file', 'err_file'],
            'level': 'WARN',
            'propagate': False
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file', 'err_file'] if DEBUG else ['file', 'err_file']
    }
}
