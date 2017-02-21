# -*- coding: utf-8 -*-
import requests
import json
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

ORDER_URL = settings.CODA_PAY_ORDER_URL
API_KEY_DICT = settings.CODA_API_KEY_DICT

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

_EXCHANGE_RATIO = settings.EXCHANGE_RATIO


def coda_create_charge(pay, pay_amount, currency, return_url=settings.PAYPAL_RETURN_URL,
                       cancel_url=settings.PAYPAL_CANCEL_URL):
    price = int(pay_amount) * _EXCHANGE_RATIO
    payload = {"initRequest": {"orderId": pay.id,
                               "profile": "",
                               "apiKey": API_KEY_DICT[currency],
                               "country": COUNTRY_CODES[currency],
                               "payType": "1",
                               "currency": CURRENCY_CODES[currency],
                               "items": [
                                   {"price": str(price),
                                    "code": "789",
                                    "type": "",
                                    "name": "Koin"}],
                               },
               }

    headers = dict()
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'

    _LOGGER.info("post data: %s" % payload)
    response = requests.post(ORDER_URL, headers=headers,
                             data=json.dumps(payload))
    response_dict = json.loads(response.text)
    if response.status_code == 200 and response_dict['initResult']['resultCode'] == 0:
        _LOGGER.error("response 200 data: %s, %s ", response_dict, payload)
        return settings.CODA_PAY_GATEWAY_URL % response_dict['initResult']['txnId']
    else:
        _LOGGER.error("response data: %s" % response_dict)
        return None


def _sign(origin_str):
    m = hashlib.md5()
    m.update(origin_str)
    sign = m.hexdigest().lower()
    return sign


def coda_check_notify(request):
    trade_no = request.GET.get('TxnId')
    pay_id = request.GET.get('OrderId')
    trade_status = request.GET.get('ResultCode')
    price = request.GET.get('TotalPrice')
    check_sum = request.GET.get('Checksum')
    pay = get_pay(pay_id)
    currency = 'IDR'
    calculated_sign = _sign("%s%s%s%s" % (
        trade_no, API_KEY_DICT[currency], pay_id, trade_status))
    _LOGGER.info("Coda Pay sign: %s, calculated sign: %",
                 check_sum, calculated_sign)
    if check_sum != calculated_sign:
        raise ParamError('sign not pass, data: %s' % request.GET)

    user_id = pay.user_id
    if not pay or pay.status != PayStatus.SUBMIT.value:
        raise ParamError('pay %s has been processed' % pay_id)

    total_fee = float(price) / _EXCHANGE_RATIO
    extend = {
        'title': u'deposit-CodaPay',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    if int(trade_status) == 0:
        _LOGGER.info('Coda Pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
            user_id, pay_id, total_fee, currency))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'coda'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception(
                    'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('Coda Pay response data show transaction failed, data: %s', request.GET)


if __name__ == '__main__':
    coda_create_charge(7236116293778989056, 66, None)
