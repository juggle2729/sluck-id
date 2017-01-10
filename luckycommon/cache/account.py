# -*- coding: utf-8 -*-

from django.conf import settings

from luckycommon.cache import ProxyAgent, prefix_key
from luckycommon.utils.decorator import cache_wrapper

_CODE_EXPIRE_TIME = 5 * 60  # 5 minutes
_IP_EXPIRE_TIME = 3600
_MAX_SENT = 2   # at most 2 sms in 5 seconds
_MAX_COUNT = 5  # if 5 req in 5 seconds then
_FORBID_TIME = 3600  # forbid this ip 5 mins


def _add_prefix(key, isIp=False):
    if isIp:
        return prefix_key('ip:%s' % key)
    else:
        return prefix_key('phone:%s' % key)


@cache_wrapper
def save_auth_code(phone, code):
    ProxyAgent().setex(_add_prefix(phone), _CODE_EXPIRE_TIME, code)


@cache_wrapper
def delete_auth_code(phone):
    ProxyAgent().delete(_add_prefix(phone))


@cache_wrapper
def get_auth_code(phone):
    return ProxyAgent().get(_add_prefix(phone))


@cache_wrapper
def get_auth_code_ttl(phone):
    return ProxyAgent().ttl(_add_prefix(phone))


@cache_wrapper
def check_count(key, max_sent, max_count, forbid_time, default_expire):
    count = ProxyAgent().get(key)
    if count is not None:
        ProxyAgent().incr(key)
        if int(count) < max_sent:
            return True
        elif int(count) >= max_count:
            ProxyAgent().expire(key, forbid_time)
            return False
        else:
            return False
    else:
        ProxyAgent().setex(key, default_expire, 1)
        return True


@cache_wrapper
def check_ip_count(ip):
    # short_key = _add_prefix(ip, True)
    # short_check = check_count(short_key, _MAX_SENT, _MAX_COUNT, _FORBID_TIME, _IP_EXPIRE_TIME)
    long_key = prefix_key('ipcount:%s' % ip)
    long_check = check_count(long_key, 6, 10, 3600, 3600)
    return long_check


@cache_wrapper
def check_phone_count(phone):
    key = prefix_key('phonecount:%s' % phone)
    phone_check = check_count(key, 10, 20, 12*3600, 12*3600)
    return phone_check


INTERNAL_IPS = ['113.57.172.122', '120.26.57.89', '120.27.162.212', '121.41.6.238']


@cache_wrapper
def check_ip_register_count(ip):
    if ip in INTERNAL_IPS:
        return True
    key = prefix_key('ipregister:%s' % ip)
    ip_check = check_count(key, 10, 20, 3600, 3600)
    return ip_check


DEVICE_REGISTER_EXPIRE = 3600


@cache_wrapper
def check_device_register_count(device_id):
    key = prefix_key('deviceregister:%s' % device_id)
    device_check = check_count(key, 2, 5, DEVICE_REGISTER_EXPIRE, DEVICE_REGISTER_EXPIRE)
    return device_check


@cache_wrapper
def check_ip_pay_limit(ip, user_id):
    key = prefix_key('ippay:%s' % ip)
    limit_info = ProxyAgent().get(key)
    if not limit_info:
        limit_info = '%s,%s' % (user_id, 10)
        ProxyAgent().setex(key, 10, limit_info)
        return True
    old_user_id, interval = limit_info.split(',')
    if user_id == int(old_user_id):
        return True
    interval = int(interval) * 2
    interval = 60 if interval > 60 else interval
    limit_info = '%s,%s' % (old_user_id, interval)
    ProxyAgent().setex(key, interval, limit_info)
    return False


@cache_wrapper
def set_image_code(user_id, code_str):
    key = prefix_key('imagecode:%s' % user_id)
    ProxyAgent().setex(key, 60, code_str)


@cache_wrapper
def get_image_code(user_id):
    key = prefix_key('imagecode:%s' % user_id)
    return ProxyAgent().get(key)


@cache_wrapper
def clear_image_code(user_id):
    key = prefix_key('imagecode:%s' % user_id)
    return ProxyAgent().delete(key)
