# -*- coding: utf-8 -*-

import hashlib
import logging

import requests

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PAY_STATUS
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_KEY = '0a79b7eb84e88c041c26a4c8660ba9d1'


def _generate_order_sign(parameter, key):
    format_str = '%s%s%s%s%s'
    origin_str = format_str % (
        parameter['uid'],
        parameter['orderid'],
        parameter['amount'],
        parameter['receiveurl'],
        key
    )
    m = hashlib.md5()
    m.update(origin_str.encode('utf8'))
    sign = m.hexdigest()
    return sign


def _generate_notify_sign(parameter, key):
    format_str = '%s%s%s%s%s%s'
    origin_str = format_str % (
        parameter['orderid'],
        parameter['result'],
        parameter['realamount'],
        parameter['dealtime'],
        parameter['cardtype'],
        key
    )
    m = hashlib.md5()
    m.update(origin_str.encode('utf8'))
    sign = m.hexdigest()
    return sign


def paypayfu_create_charge(pay, pay_amount):
    parameter_dict = {
        'uid': '8039',
        'orderid': pay.id,
        'title': u'一元购-%s' % pay.id,
        'amount': pay_amount,
        'receiveurl': 'http://www.baidu.com',
        'userIP': '127.0.0.1',
    }
    parameter_dict['sign'] = _generate_order_sign(parameter_dict, _KEY)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('http://www.paypayfu.com/i/utf8/zfbwap/', data=parameter_dict, headers=headers)
    return response.text


def check_notify_sign(request):
    data = request.GET
    _LOGGER.info("paypayfu notify data: %s", data)
    sign = data['sign']
    calculated_sign = _generate_notify_sign(data, _KEY)
    if sign.lower() != calculated_sign:
        _LOGGER.info("paypayfu sign: %s, calculated sign: %", sign, calculated_sign)
        raise ParamError('sign not pass, data: %s' % data)
    pay_id = data['orderid']
    if not pay_id:
        _LOGGER.error("fatal error, out_trade_no not exists, data: %s" % data)
        raise ParamError('paypayfu event does not contain pay ID')

    pay = get_pay(pay_id)
    if not pay or pay.status != PAY_STATUS.SUBMIT:
        raise ParamError('pay %s has been processed' % pay_id)

    trade_status = int(data['result'])
    user_id = pay.user_id
    trade_no = data['orderid']
    total_fee = float(data['realamount'])

    extend = {
        'title': u'充值-微信支付',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }

    update_pay_ext(pay_id, extend['ext'])

    if trade_status == 1:
        _LOGGER.info('paypayfu check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'paypayfu'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('paypayfu response data show transaction failed, data: %s', data)


if __name__ == '__main__':
    class PayDemo(object):
        id = None
        user_id = None


    pay_demo = PayDemo()
    pay_demo.id = 7235943658131054848
    pay_demo.user_id = 491
    print paypayfu_create_charge(pay_demo, 0.01)
