# -*- coding: utf-8 -*-
import hashlib
import logging

import requests
from django.conf import settings

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PAY_STATUS
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_SHENFUTONG_KEY = '44F3411D4C4A490F91D2D16C893C5145'
_SHENFUTONG_APP_ID = 1681
_SHENFUTONG_MER_ID = '21100600801'


def generate_sign(parameter, key):
    s = ''
    for k in sorted(parameter.keys()):
        s += '%s=%s&' % (k, parameter[k])
    s = s.strip('&')
    s += key
    m = hashlib.md5()
    m.update(s.encode('utf8'))
    sign = m.hexdigest()
    return sign


def shenfutong_create_charge(pay, pay_amount):
    parameter_dict = {
        'merId': _SHENFUTONG_MER_ID,
        'appId': _SHENFUTONG_APP_ID,
        'merOrderId': str(pay.id),
        'payerId': str(pay.user_id),
        # 'reqFee': str(int(pay_amount * 100)),
        'reqFee': '1',
        'itemName': 'yiyuangou-%s' % pay.id,
        'returnUrl': settings.SHENFUTONG_RETURN_URL,
        'notifyUrl': settings.SHENFUTONG_NOTIFY_URL,
    }
    parameter_dict['signValue'] = generate_sign(parameter_dict, _SHENFUTONG_KEY)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('http://payment-test.szhuyu.com/wap/alipay/th', data=parameter_dict, headers=headers)
    return response.text


def check_notify_sign(request):
    data = dict(request.POST.iteritems())
    sign = data.pop('signValue')
    data.pop('extInfo')
    calculated_sign = generate_sign(data, _SHENFUTONG_KEY)
    _LOGGER.info("shenfutong sign: %s, calculated sign: %s" % (sign, calculated_sign))
    if sign != calculated_sign:
        raise ParamError('sign not pass, data: %s' % data)
    pay_id = data['merOrderId']
    if not pay_id:
        _LOGGER.error("fatal error, merOrderId not exists, data: %s" % data)
        raise ParamError('shenfutong notify does not contain pay ID')

    pay = get_pay(pay_id)
    if not pay or pay.status != PAY_STATUS.SUBMIT:
        raise ParamError('pay %s has been processed' % pay_id)

    trade_status = int(data['orderStatus'])
    user_id = pay.user_id
    trade_no = data['orderId']
    total_fee = data['amount']
    total_fee = float(total_fee) / 100

    extend = {
        'title': u'充值-支付宝支付',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }

    update_pay_ext(pay_id, extend['ext'])

    if trade_status == 0:
        _LOGGER.info('shenfutong check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'shenfutong'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('shenfutong response data show transaction failed, data: %s', data)
