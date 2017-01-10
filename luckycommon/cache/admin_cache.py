# -*- coding: utf-8 -*-

""" 控制台专用的一些缓存项
"""

import logging

from luckycommon.cache import ProxyAgent, prefix_key
from luckycommon.utils.decorator import cache_wrapper

_LOGGER = logging.getLogger('lucky')


@cache_wrapper
def set_jd_token(token, expired):
    k = prefix_key('jdtoken', 'luckyadmin')
    ProxyAgent().setex(k, expired, token)


@cache_wrapper
def get_jd_token():
    return ProxyAgent().get(prefix_key('jdtoken', 'luckyadmin'))


@cache_wrapper
def get_goods_list():
    return ProxyAgent().hgetall(prefix_key('goods', 'luckyadmin'))


@cache_wrapper
def set_goods_list(id_name_dict):
    key = prefix_key('goods', 'luckyadmin')
    ProxyAgent().hmset(key, id_name_dict)


@cache_wrapper
def upsert_goods(id, name):
    key = prefix_key('goods', 'luckyadmin')
    ProxyAgent().hset(key, id, name)


@cache_wrapper
def delete_goods(id):
    key = prefix_key('goods', 'luckyadmin')
    ProxyAgent().hdel(key, id)
