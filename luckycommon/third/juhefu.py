# -*- coding: utf-8 -*-

import hashlib
import logging

import re
import requests

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PAY_STATUS
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_KEY = 'sv01t2m62p'


def generate_order_sign(parameter, key):
    format_str = 'version=%s&merid=%s&mername=%s&merorderid=%s&paymoney=%s&productname=%s&productdesc=%s&userid=%s&username=%s&email=%s&phone=%s&extra=%s&custom=%s&redirecturl=%s'
    origin_str = format_str % (
        parameter['version'],
        parameter['merid'],
        parameter['mername'],
        parameter['merorderid'],
        parameter['paymoney'],
        parameter['productname'],
        parameter['productdesc'],
        parameter['userid'],
        parameter['username'],
        parameter['email'],
        parameter['phone'],
        parameter['extra'],
        parameter['custom'],
        parameter['redirecturl'],
    ) + key
    m = hashlib.md5()
    m.update(origin_str.encode('utf8'))
    sign = m.hexdigest()
    return sign


def generate_notify_sign(parameter, key):
    format_str = 'version=%s&merid=%s&merorderid=%s&tradeid=%s&tradedate=%s&success=%s&successmoney=%s&paychannel=%s&channeltradeid=%s&cardid=%s&userid=%s&username=%s&extra=%s&attach=%s&internal=%s'
    origin_str = format_str % (
        parameter['version'],
        parameter['merid'],
        parameter['merorderid'],
        parameter['tradeid'],
        parameter['tradedate'],
        parameter['success'],
        parameter['successmoney'],
        parameter['paychannel'],
        parameter['channeltradeid'],
        parameter['cardid'],
        parameter['userid'],
        parameter['username'],
        parameter['extra'],
        parameter['attach'],
        parameter['internal'],
    ) + key
    m = hashlib.md5()
    m.update(origin_str.encode('utf8'))
    sign = m.hexdigest()
    return sign


def juhefu_create_charge(pay, pay_amount):
    parameter_dict = {
        'version': '1.0',
        'merid': '26100951',
        'mername': u'武汉卓翰网络科技有限公司',
        'merorderid': pay.id,
        'paymoney': pay_amount,
        'productname': u'一元购-%ssp' % pay.id,
        'productdesc': u'夺宝币',
        'userid': pay.user_id,
        'username': u'用户',
        'email': '',
        'phone': '',
        'extra': '',
        'custom': '',
        'redirecturl': '',
    }
    parameter_dict['md5'] = generate_order_sign(parameter_dict, _KEY)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('http://www.jhpay.com/wechat/wechatpay.jsp', data=parameter_dict, headers=headers)
    url = re.findall(r'(https.*wappayv\d)', response.text)[0]
    return url


def check_notify_sign(request):
    data = request.POST
    _LOGGER.info("juhefu notify data: %s", data)
    sign = data['md5']
    calculated_sign = generate_notify_sign(data, _KEY)
    if sign.lower() != calculated_sign:
        _LOGGER.info("juhefu sign: %s, calculated sign: %", sign, calculated_sign)
        raise ParamError('sign not pass, data: %s' % data)
    pay_id = data['merorderid']
    if not pay_id:
        _LOGGER.error("fatal error, out_trade_no not exists, data: %s" % data)
        raise ParamError('swiftpass event does not contain pay ID')

    pay = get_pay(pay_id)
    if not pay or pay.status != PAY_STATUS.SUBMIT:
        raise ParamError('pay %s has been processed' % pay_id)

    trade_status = int(data['success'])
    user_id = pay.user_id
    trade_no = data['tradeid']
    total_fee = float(data['successmoney'])

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
        _LOGGER.info('juhefu check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'juhefu'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('juhefu response data show transaction failed, data: %s', data)


if __name__ == '__main__':
    class PayDemo(object):
        id = None
        user_id = None


    pay_demo = PayDemo()
    pay_demo.id = 7235943658031054848
    pay_demo.user_id = 491
    print juhefu_create_charge(pay_demo, 0.01)
