# -*- coding: utf-8 -*-
import requests
import json
from random import randint
import logging
import hashlib

from django.conf import settings
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_BLUEPAY_KEY = 'VMM91GP7Aq8EAD22'
_EXCHANGE_RATIO = settings.EXCHANGE_RATIO

COUNTRY_CODES = {
    'SGD': '702',
    'IDR': '360',
    'MYR': '458',
    'THB': '764',
    'PHP': '608',
    'VND': '704',
    'TWD': '158',
    'LKR': '144',
}

CURRENCY_CODES = {
    'SGD': '702',
    'IDR': '360',
    'MYR': '458',
    'THB': '764',
    'PHP': '608',
    'VND': '704',
    'TWD': '901',
    'LKR': '144',
}


def _sign(origin_str):
    m = hashlib.md5(origin_str+_BLUEPAY_KEY)
    sign = m.hexdigest().lower()
    return sign


def bluepay_check_notify(request):
    path = request.get_full_path()
    checkpath = path[path.index('?')+1 : path.index('&encry')]
    cmd = request.GET.get('cmd')
    pay_id = request.GET.get('t_id')
    msisdn = request.GET.get('msisdn')
    price = request.GET.get('price')
    operator = request.GET.get('operator')
    paytype = request.GET.get('paytype')
    encry = request.GET.get('encrypt')
    currency = request.GET.get('currency')
    status = request.GET.get('status')
    trade_no = request.GET.get('bt_id')
    pay = get_pay(pay_id)
    
    _LOGGER.error('bluepay notify, path %s', path[path.index('?')+1:path.index('&encry')])
    _LOGGER.error('bluepay notify, sign %s, encry %s', _sign(checkpath), encry)
    if _sign(checkpath) != encry:
        raise ParamError('sign not pass, data: %s' % request.GET)
    
    user_id = pay.user_id
    if not pay or (pay.status != PayStatus.SUBMIT.value and pay.status != PayStatus.FAIL.value):
        raise ParamError('pay %s has been processed' % pay_id)

    total_fee = float(price) / _EXCHANGE_RATIO
    extend = {
        'title': u'deposit-BluePay',
        'ext': {
            'trade_status': status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    if int(status) == 200:
        _LOGGER.info('Blue Pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
            user_id, pay_id, total_fee, currency))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'bluepay'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception(
                    'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('BluePay response data show transaction failed, data: %s', request.GET)


if __name__ == '__main__':
    pay = {'id': 'sndbox_' + str(randint(1000,13333))}
    doku_create_charge(pay, 66, 'IDR')
