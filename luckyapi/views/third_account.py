# -*- coding: utf-8 -*-
import logging
import pyDes

from django.conf import settings
from django.views.decorators.http import require_POST

from luckyapi.logic.account import get_fixed_num

from luckycommon.push import handler as push_handler
from luckycommon.model.account import THIRD_ACCOUNT_TYPE
from luckycommon.db.account import (exists_phone, get_third_account,
                                    third_account_login, register_third_account)
from luckycommon.db.transaction import add_system_award_transaction

from luckycommon.utils.api import token_required, get_client_ip, get_city
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError, AuthenticateError
from luckycommon.cache.redis_cache import is_uxin_login_credential_valid, invalid_uxin_login_credential

from future.utils import raise_with_traceback


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')

DES_KEY = '!@#$uxin'


def _get_user_info(user):
    phone_num = user.phone[2:]
    return {
        'id': str(user.id),
        'phone': phone_num,
        'avatar_id': user.avatar_id,
        'nick_name': user.nick_name,
        'email': user.email,
        'balance': user.balance,
        'country': user.country,
        'token': user.token
    }


@require_POST
@response_wrapper
def uxin_login(request):
    try:
        pnum = request.POST.get('pnum').decode("base64")
        ts = request.POST.get('ts')
        uid = request.POST.get('uid')
        client_ip = get_client_ip(request)
        client_city = get_city(client_ip)
        extend = {
            'ip': client_ip,
            'addr': client_city
        }
        _LOGGER.info("pnum: %s, ts: %s, uid: %s" % (pnum.encode("base64"), ts, uid))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    k = pyDes.des(DES_KEY, pyDes.CBC, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
    try:
        d = k.decrypt(pnum)
        phone_number, time_stamp = d.split('#')
        phone_number = get_fixed_num(phone_number)
        _LOGGER.info("d: %s, phone: %s, timestamp: %s, ts: %s" % (d, phone_number, time_stamp, ts))
        if time_stamp != ts:
            raise ParamError('ts invalid')
    except Exception as e:
        _LOGGER.exception('Des decrypt fail.(%s)' % e)
        raise ParamError('Des auth error.')

    if not is_uxin_login_credential_valid(phone_number, time_stamp):
        raise AuthenticateError('Uxin login credential invalid, the request URL is a one shot URL.')

    third_account = get_third_account(login_type=THIRD_ACCOUNT_TYPE.UXIN, phone_number=phone_number)
    if third_account:
        # exists, auto login
        login_user, logon = third_account_login(third_account.user_id, device_type='', os_version='', extend=extend)
        _TRACKER.info({"user_id": login_user.id, "type": "login", "logon": logon})
        invalid_uxin_login_credential(phone_number, time_stamp)
        return _get_user_info(login_user)
    else:
        # check if native account
        exists_account = exists_phone(phone_number)
        if not exists_account:
            # register
            account_info = {
                'phone': phone_number,
                'nick_name': '%s****%s' % (phone_number[2:][:3], phone_number[2:][-4:]),
                'country': settings.COUNTRY,
                'avatar': '',
                'avatar_id': '',
                'email': ''
            }
            third_account = register_third_account(account_info, login_type=THIRD_ACCOUNT_TYPE.UXIN, login_id=uid)
            _TRACKER.info({"user_id": third_account.user_id, "type": "register",
                           "aid": 'none',
                           "chn": 'uxin'})
            # add system award
            try:
                add_system_award_transaction(third_account.user_id)
                push_handler.push_fresh_award(third_account.user_id)
            except Exception as e:
                _LOGGER.error('add award error.(%s)' % e)

            login_user, logon = third_account_login(third_account.user_id, device_type='', os_version='', extend=extend)
            _TRACKER.info({"user_id": login_user.id, "type": "login", "logon": logon})
            invalid_uxin_login_credential(phone_number, time_stamp)
            user_info = _get_user_info(login_user)
            user_info.update({'first_login': True})
            return user_info
        else:
            raise AuthenticateError('need password')
