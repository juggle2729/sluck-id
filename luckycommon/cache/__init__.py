# -*- coding: utf-8 -*-
import redis
import logging
import functools

from redis.exceptions import ConnectionError
from django.conf import settings

_LOGGER = logging.getLogger(__name__)

_MAX_TRY_COUNT = 3
_REDIS_KEY_PREFIX = 'lucky'


def singleton(cls):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


@singleton
class ProxyAgent(object):
    def __init__(self):
        self.client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    def __wrap(self, method, *args, **kwargs):
        try_count = 0
        while try_count < _MAX_TRY_COUNT:
            try:
                f = getattr(self.client, method)
                return f(*args, **kwargs)
            except Exception, e:
                try_count += 1
                _LOGGER.exception(
                    "Redis connection error.%s try(%d)" % (e, try_count))
                if try_count >= _MAX_TRY_COUNT:
                    raise ConnectionError(
                        "Redis connection reached max tries(%d)." % try_count)
                continue

    def __getattr__(self, method):
        return functools.partial(self.__wrap, method)


def prefix_key(key):
    return '%s:%s' % (_REDIS_KEY_PREFIX, key)
