# -*- coding: utf-8 -*-
import time
import logging
from datetime import timedelta
from django.conf import settings

from luckyapi.logic import coupon as coupon_handler

from luckycommon.async.async_job import send_authcode

from luckycommon.utils.tz import local_now, local_to_utc
from luckycommon.utils.id_generator import generate_auth_code

from luckycommon.cache import account as cache
from luckycommon.third.image import upload_data, delete_data_by_url
from luckycommon.third.sms.helper import send_sms

_LOGGER = logging.getLogger('lucky')


def send_auth_code(phone, country=None, ip='', need_check=True):
    if need_check:
        if ip and not cache.check_ip_count(ip):
            _LOGGER.error('same ip send sms too quick!!!, ip:%s, phone:%s', ip, phone)
            return None
        if not cache.check_phone_count(phone):
            _LOGGER.error('same phone send sms too quick!!!, ip:%s, phone: %s', ip, phone)
            return None
    code = cache.get_auth_code(phone)
    if not code:
        code = generate_auth_code()
        cache.save_auth_code(phone, code)
    try:
        send_authcode.delay(phone, code, country)
        _LOGGER.info(', ip:%s, phone:%s', ip, phone)
    except Exception as e:
        cache.delete_auth_code(phone)
        raise e
    return code


def check_auth_code(phone, code):
    saved_code = cache.get_auth_code(phone)
    # FIXME: this code for test only
    return saved_code == code # or code == '12345678'


def upload_avatar(avatar_data, prev_url=''):
    #if prev_url:
    #    delete_data_by_url([prev_url], bucket=settings.USER_BUCKET_NAME,
    #                       key_prefix='avatars')
    #return upload_data(avatar_data, key_prefix='avatars')
    return ''


def add_fresh_coupon(user_id):
    local_today = local_now().replace(hour=0, minute=0, second=0)
    # 满2减1
    coupon_handler.send_coupon_to_user(user_id, 132, 1)
    # 满10减2, 第二天
    start_date = local_today + timedelta(1)
    start_ts = int(time.mktime(local_to_utc(start_date).timetuple()))
    coupon_handler.send_coupon_to_user(user_id, 133, 1, start_ts=start_ts)
    # 满50减5
    start_date = local_today + timedelta(2)
    start_ts = int(time.mktime(local_to_utc(start_date).timetuple()))
    coupon_handler.send_coupon_to_user(user_id, 134, 1, start_ts=start_ts)
    # 满100减10
    start_date = local_today + timedelta(6)
    start_ts = int(time.mktime(local_to_utc(start_date).timetuple()))
    coupon_handler.send_coupon_to_user(user_id, 135, 1, start_ts=start_ts)
