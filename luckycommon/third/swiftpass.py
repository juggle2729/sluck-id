# -*- coding: utf-8 -*-
"""
http://www.swiftpass.cn/
"""
import hashlib
import logging

import requests
import xmltodict
from dicttoxml import dicttoxml
from django.conf import settings

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PAY_STATUS
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_MCH_ID_DICT = {
    'WEIXIN_WAP': u'7101000035',
    'ALI_SDK': u'710265000007',
}
_SWIFTPASS_KEY_DICT = {
    'WEIXIN_WAP': '1548379be8cc2e39f916d89301bb475c',
    'ALI_SDK': 'e8a87ee01cbe476de6964ef4',
    'pay.weixin.wappay': '1548379be8cc2e39f916d89301bb475c',
    'unified.trade.pay': 'e8a87ee01cbe476de6964ef4',
}
_SERVICE_DICT = {
    'WEIXIN_WAP': u'pay.weixin.wappay',
    'ALI_SDK': u'unified.trade.pay',
}
_TYPE_DICT = {
    'pay.alipay.app': u'支付宝',
    'pay.weixin.wappay': u'微信',
}


def generate_sign(parameter, key):
    s = ''
    for k in sorted(parameter.keys()):
        s += '%s=%s&' % (k, parameter[k])
    s += 'key=%s' % key
    m = hashlib.md5()
    m.update(s.encode('utf8'))
    sign = m.hexdigest().upper()
    return sign


def swiftpass_create_charge(pay, pay_amount, service):
    parameter_dict = {
        'service': _SERVICE_DICT[service],
        'version': '1.0',
        'mch_id': _MCH_ID_DICT[service],
        'out_trade_no': pay.id,
        'body': u'一元购-%s' % pay.id,
        'total_fee': int(pay_amount * 100),
        'mch_create_ip': u'127.0.0.1',
        'notify_url': settings.SWIFTPASS_NOTIFY_URL,
        # 'callback_url': 'http://121.41.6.238:9898/',
        'nonce_str': pay.id,
    }
    parameter_dict['sign'] = generate_sign(parameter_dict, _SWIFTPASS_KEY_DICT[service])
    xml_data = dicttoxml(parameter_dict)
    headers = {'Content-Type': 'application/xml'}
    _LOGGER.info("swiftpass data: %s", xml_data)
    response = requests.post('https://pay.swiftpass.cn/pay/gateway', data=xml_data, headers=headers, timeout=1).text
    response_json = xmltodict.parse(response)
    return response_json


def check_notify_sign(request):
    data = xmltodict.parse(request.body)['xml']
    sign = data['sign']
    data.pop('sign')
    trade_type = data['trade_type']
    calculated_sign = generate_sign(data, _SWIFTPASS_KEY_DICT[trade_type])
    if sign != calculated_sign:
        _LOGGER.info("swiftpass sign: %s, calculated sign: %", sign, calculated_sign)
        raise ParamError('sign not pass, data: %s' % data)
    pay_id = data['out_trade_no']
    if not pay_id:
        _LOGGER.error("fatal error, out_trade_no not exists, data: %s" % data)
        raise ParamError('swiftpass event does not contain pay ID')

    pay = get_pay(pay_id)
    if not pay or pay.status != PAY_STATUS.SUBMIT:
        raise ParamError('pay %s has been processed' % pay_id)

    trade_status = int(data['pay_result'])
    user_id = pay.user_id
    trade_no = data['transaction_id']
    total_fee = data['total_fee']
    total_fee = float(total_fee) / 100

    extend = {
        'title': u'充值-%s' % _TYPE_DICT[trade_type],
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }

    update_pay_ext(pay_id, extend['ext'])

    if trade_status == 0:
        _LOGGER.info('swiftpass check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'swiftpass'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('swiftpass response data show transaction failed, data: %s', data)
