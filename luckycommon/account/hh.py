# -*- coding: utf-8 -*-
import re
import time
import urllib
import base64
import logging
from pyDes import *
from datetime import datetime, timedelta

from luckyapi.logic import coupon as coupon_handler
from luckycommon.account.db.account import get_third_account_by_uid
from luckycommon.level.handler import get_level_dict

from luckycommon.cache import account as cache
from luckycommon.account.db import account as account_db
from luckycommon.db import partner as partner_db
from luckycommon.utils.respcode import StatusCode

from luckycommon.utils.tz import now_ts, local_now, local_to_utc
from luckycommon.utils import exceptions as err
from luckycommon.utils.template import generate_from_template
from luckycommon.utils.id_generator import generate_auth_code

from luckycommon.third.sms.helper import send_sms
from luckycommon.third.email_provider import send_mail

from django.conf import settings

_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')

_DEFAULT_PAGE_SIZE = 20

RE_PHONE = re.compile(r'^1\d{10}$')
RE_EMAIL = re.compile(r'^.*@.+\..+$')
DES_COM = des("LUCKYGOU", CBC, "\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)


def _send_email_auth_code(email_num, auth_code):
    email_content = generate_from_template('email_auth_code', {'code': auth_code}, has_title=False)
    send_mail(email_num, u'邮箱验证码', email_content)


def _send_email_resetpwd_link(email_num, link_code):
    link_code = '%s/reset_password?code=%s' % (settings.WEB_APP_ROOT_URL, urllib.quote(link_code))
    email_content = generate_from_template('email_reset_pwd', {'nick_name': email_num, 'code': link_code}, has_title=False)
    send_mail(email_num, 'reset password', email_content)
    _LOGGER.info('send email resetpwd link %s', link_code)


def _create_auth_code(send_num):
    code = cache.get_auth_code(send_num)
    if not code:
        code = generate_auth_code()
        cache.save_auth_code(send_num, code)
    else:
        ttl = cache.get_auth_code_ttl(send_num)
        # if int(ttl) > 1200:
        #    raise err.ClientError()
        # update
        code = generate_auth_code()
        cache.save_auth_code(send_num, code)
    return code


def send_auth_code(send_num, send_by):
    code = _create_auth_code(send_num)
    try:
        if send_by == 'email':
            _send_email_auth_code(send_num, code)
            _LOGGER.info('send email succ, email:%s', send_num)
        else:
            send_sms([send_num], 'auth_code', {'code': code})
            _LOGGER.info('send sms succ, phone:%s, auth_code: %s' % (send_num, code))
    except Exception as e:
        cache.delete_auth_code(send_num)
        raise e
    return code


def send_resetpwd_link(email):
    send_num = email
    code = _create_auth_code(send_num)
    link_str = str('%s:%s:%s' % (send_num, code, now_ts()))
    d = DES_COM.encrypt(link_str)
    link_code = base64.b64encode(d)
    _send_email_resetpwd_link(send_num, link_code)
    return link_code


def reset_password(phone, new_password):
    account = account_db.get_account_by_phone(phone)
    if not account:
        raise err.DataError(status=StatusCode.INVALID_USER)

    account_db.reset_passwd(account, new_password)
    account_db.logout_user(account.id)
    _TRACKER.info({"user_id": account.id, "type": "reset_pwd"})


def check_auth_code(num, code):
    saved_code = cache.get_auth_code(num)
    _LOGGER.info("input auth code: %s, auth code: %s" % (code, saved_code))
    # FIXME: this code for test only
    return saved_code == code  # or code == '12345678'


def check_register_num(register_num):
    register_type = 'phone'
    return register_type, register_num


def get_user_type(account):
    if not account.created_at:
        # 新用户
        return 1
    registered_at = account.created_at.date()
    now_dt = datetime.utcnow().date()
    if now_dt == registered_at:
        # 新用户
        return 1
    elif now_dt - registered_at == timedelta(days=1):
        # 次日用户
        return 2
    elif now_dt - registered_at <= timedelta(days=6):
        # 周用户
        return 3
    else:
        # 老用户
        return 4


def get_user_info(user):
    inviter_item = partner_db.get_user_inviter(user.id)
    level_dict = get_level_dict(user.id)
    third_account = get_third_account_by_uid(user.id)
    data = {
        'id': str(user.id),
        'type': get_user_type(user),
        'phone': user.phone if user.phone else "",
        'avatar_id': user.avatar_id if user.avatar_id else "",
        'nick_name': user.nick_name if user.nick_name else "",
        'desc': user.desc if user.desc else "",
        'email': user.email if user.desc else "",
        'balance': user.balance,
        'credit': user.credit,
        'country': user.country if user.country else "",
        'token': user.token,
        'level': level_dict['current_level'],
        'level_icon': level_dict['level_icon'],
        'level_name': level_dict['level_name'],
        'third_bind': '' if not third_account else third_account.third_account_type,
    }
    if inviter_item:
        inviter_id = inviter_item.inviter_id
        inviter_account = account_db.get_account(inviter_id)
        data.update({
            'inviter_id': inviter_id,
            'inviter_name': inviter_account.nick_name
        })
    return data


def get_user_info_by_uid(user_id):
    user = account_db.get_user_by_uid(user_id)
    if user:
        data = {
            'id': user.id,
            'nick_name': user.nick_name,
            'avatar_id': user.avatar_id,
        }
        return data
    return None


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
