# -*- coding: utf-8 -*-
import hashlib
import json
import logging
from collections import OrderedDict

import requests
from django.conf import settings

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_fail_transaction
from luckycommon.db.transaction import add_pay_success_transaction
from luckycommon.model.pay import PayStatus, PayType
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import (ParamError, DataError, ServerError, AuthenticateError)

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_MERCHANT_ID = '47687'
_MERCHANT_ACCOUNT = 'luckysky.jsc@gmail.com'
_MERCHANT_PASSWD = 'd3d3807c1c50b1962e3e35eaf8eed510'
_MERCHANT_PASSWD_HASH = hashlib.md5('|'.join([_MERCHANT_ID, _MERCHANT_PASSWD])).hexdigest()

_EWALLET_URL = "https://www.nganluong.vn/mobile_checkout_api_post.php"

_EWALLET_ERR_DICT = {
    '00': 'pay success',
    '01': 'Unknown error',
    '02': 'merchant_id not exist',
    '04': 'checksum not match',
    '05': 'No orders recorded on payment gateway',
    '06': 'token_code not exist or is invalid',
    '07': 'Unpaid orders'
}

_EWALLET_AMOUNT_MIN = 2000

_EXCHANGE_RATIO = settings.EXCHANGE_RATIO


def ewallet_send_order(pay, pay_amount):

    pay_id = pay.id
    pay_amount = int(pay_amount) * _EXCHANGE_RATIO
    try:
        if int(pay_amount) < _EWALLET_AMOUNT_MIN:
            raise ParamError('pay amount must gte %s' % _EWALLET_AMOUNT_MIN)
    except:
        raise ParamError('pay amount invalid')

    payload = OrderedDict((
        ('func', 'sendOrder'),
        ('version', '1.0'),
        ('merchant_id', _MERCHANT_ID),
        ('merchant_account', _MERCHANT_ACCOUNT),
        ('order_code', str(pay_id)),
        ('total_amount', str(pay_amount)),
        ('currency', 'vnd'),
        ('language', 'vi'),
        ('return_url', "%s/%s" % (settings.NGANLUONG_RETURN_URL, pay_id)),
        ('cancel_url', settings.NGANLUONG_CLOSE_URL),
        ('notify_url', settings.NGANLUONG_NOTIFY_URL),
        ('buyer_fullname', 'test'),
        ('buyer_email', 'test@test.com'),
        ('buyer_mobile', '0986588099'),
        ('buyer_address', '')
    ))
    string_a = '|'.join(payload.values())
    string_b = '|'.join([string_a, _MERCHANT_PASSWD])
    checksum = hashlib.md5(string_b).hexdigest()
    payload['checksum'] = checksum
    _LOGGER.debug('Nganluong ewallet ready to send order, pay_id[%s], payload: %s' % (pay_id, payload))
    r = requests.post(_EWALLET_URL, payload)
    if r.status_code == 200:
        _LOGGER.debug('call Nganluong  ewallet send order api success, response:%s' % r.text)
        ret_dict = json.loads(r.text)
        if ret_dict['response_code'] == '00':
            # update token code to pay
            token_code = ret_dict['token_code']
            checkout_url = ret_dict['checkout_url']
            ext = {
                'token_code': token_code,
                'checkout_url': checkout_url
            }
            update_pay_ext(pay_id, ext)
            return checkout_url
        else:
            _LOGGER.error('e-wallet send order fail, pay_id:%s response_code:%s' %
                          (pay_id, ret_dict['response_code']))
    else:
        raise ServerError('nganluong ewallet api not access')

    return None


def ewallet_check_order(pay_id, token_code=None):
    pay = get_pay(pay_id)

    user_id = pay.user_id
    pay_id = pay.id

    extend = json.loads(pay.extend)
    if token_code:
        if token_code != extend['token_code']:
            raise DataError('token code [%s] not refer to pay [%s]' % (token_code, pay_id))
    token_code = extend['token_code']

    payload = OrderedDict((
        ('func', 'checkOrder'),
        ('version', '1.0'),
        ('merchant_id', _MERCHANT_ID),
        ('token_code', token_code)
    ))
    stringA = '|'.join(payload.values())
    stringB = '|'.join([stringA, _MERCHANT_PASSWD])
    checksum = hashlib.md5(stringB).hexdigest()
    payload['checksum'] = checksum
    r = requests.post(_EWALLET_URL, payload)
    if r.status_code != 200:
        _LOGGER.error('e-wallet check order fail. pay_id[%s] token_code[%s]' % (pay_id, token_code))
        raise ServerError('nganluong check order api not access')

    _LOGGER.debug('call ewallet check order api success, response:%s' % r.text)
    ret_dict = json.loads(r.text)
    if ret_dict['response_code'] == '00':
        total_fee = float(ret_dict['total_amount']) / _EXCHANGE_RATIO
        extend = {
            'title': u'NganLuong-recharge',
            'success': True,
            'ext': ret_dict
        }
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.info('NganLuong e-wallet Pay check order success, user_id:%s pay_id:%s, amount: %s' % (user_id, pay_id, total_fee))
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'NganLuong'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        raise DataError('NganLuong response data show transaction not done')


def handle_notify(request):
    data = dict(request.POST.iteritems())
    _LOGGER.info("Nganluong Pay notify data: %s", data)
