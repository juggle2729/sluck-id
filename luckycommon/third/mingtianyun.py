# -*- coding: utf-8 -*-

import hashlib
import logging
import json

from django.conf import settings

from luckyapi.model.transaction import available_pay_types
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PAY_STATUS
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError
from luckycommon.utils.ip_address import get_ip_address

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_APP_ID = '0000000063'
_KEY = 'f7f09e929dfa8a33ea92bff1421f9059'


def generate_sign(parameter, key):
    s = ''
    for k in sorted(parameter.keys()):
        if parameter[k] != "":
            s += '%s=%s&' % (k, parameter[k])
    s += 'key=%s' % key
    m = hashlib.md5()
    m.update(s.encode('utf8'))
    _LOGGER.info(u'origin string: %s' % s)
    sign = m.hexdigest()
    return sign


def mingtianyun_create_charge(pay, pay_amount, channel):
    parameter_dict = {
        'version': 'android_v1_0_5',
        'amount': int(pay_amount * 100),
        'appid': _APP_ID,
        'body': u'夺宝币（客服电话：4008807161）',
        'payChannelId': channel,
        'mchntOrderNo': pay.id,
        'notifyUrl': settings.MINGTIANYUN_NOTIFY_URL,
        'subject': u'一元购-%smty' % pay.id,
        'clientIp': get_ip_address('eth1')
    }
    sign = generate_sign(parameter_dict, _KEY)
    parameter_dict['signature'] = sign
    return parameter_dict


def check_notify_sign(request):
    data = json.loads(request.body)
    sign = data.pop('signature')
    calculated_sign = generate_sign(data, _KEY)
    if sign.lower() != calculated_sign:
        _LOGGER.info("mingtianyun sign: %s, calculated sign: %", sign, calculated_sign)
        raise ParamError('sign not pass, data: %s' % data)
    pay_id = data['mchntOrderNo']
    if not pay_id:
        _LOGGER.error("fatal error, out_trade_no not exists, data: %s" % data)
        raise ParamError('mingtianyun event does not contain pay ID')

    pay = get_pay(int(pay_id))
    if not pay:
        raise ParamError('pay_id: %s invalid' % pay_id)
    if pay.status != PAY_STATUS.SUBMIT:
        raise ParamError('pay %s has been processed' % pay_id)

    trade_status = int(data['paySt'])
    user_id = pay.user_id
    trade_no = data['orderNo']
    total_fee = float(data['amount']) / 100

    extend = {
        'title': u'充值-%s支付' % available_pay_types[pay.pay_type].get('name'),
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }

    update_pay_ext(pay_id, extend['ext'])

    if trade_status == 2:
        _LOGGER.info('mingtianyun check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'mingtianyun'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('mingtianyun response data show transaction failed, data: %s', data)


if __name__ == '__main__':
    class PayDemo(object):
        id = None
        user_id = None


    pay_demo = PayDemo()
    pay_demo.id = 7235943658031054848
    pay_demo.user_id = 491
    print mingtianyun_create_charge(pay_demo, 0.01, 'DLCallBack.PAY_WITH_ZHIFUBAO')
