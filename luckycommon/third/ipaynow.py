# -*- coding: utf-8 -*-

import urllib
import urlparse
import hashlib
import time
import logging
from datetime import datetime
from pytz import timezone

from django.conf import settings
from luckycommon.utils.exceptions import DataError, ParamError
from django.utils.encoding import smart_unicode
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.model.pay import PAY_TYPE, PAY_STATUS
from luckycommon.db.transaction import (add_pay_wait_transaction,
                                        add_pay_success_transaction,
                                        add_pay_fail_transaction)
from luckycommon.pay.handler import pay_after_recharge

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

APPID = "1451901945016118"
APPKEY = "W56oXd1t9Ci6RPJgM6nFE86gB1KkDe8V"


def ipaynow_encrypt(encrypt_params, origin_params, app_key):
    h = hashlib.md5()
    h.update(app_key)
    app_key_hash = h.hexdigest()
    sorted_params = sorted(encrypt_params, key=lambda item: item[0])
    param_array = [item[0] + '=' + str(item[1]) for item in sorted_params]
    param_array.append(app_key_hash)
    param_str = "&".join(param_array)
    print(param_str)
    m = hashlib.md5()
    m.update(param_str)
    signature = m.hexdigest()
    result_array = encrypt_params + origin_params + [('mhtSignature', signature)]
    url = """https://api.ipaynow.cn/?""" + urllib.urlencode(result_array)
    return url


def ipaynow_create_charge(pay, pay_amount, pay_type, return_url):
    encrypt_params = [
        ('mhtOrderType', '01'),
        ('mhtCurrencyType', '156'),
        ('mhtOrderDetail', 'capacityeps'),
        ('mhtCharset', 'UTF-8'),
        ('mhtOrderName', "capacityeps"),
        ('appId', APPID),
        ('notifyUrl', settings.IPAYNOW_NOTIFY_URL),
        ('frontNotifyUrl', return_url),
        ('mhtOrderStartTime', datetime.now(timezone('Asia/Shanghai')).strftime('%Y%m%d%H%M%S')),
        ('mhtOrderNo', pay.id),
        ('mhtOrderAmt', int(pay_amount * 100)),
    ]
    origin_params = [
        ('funcode', 'WP001'),
        ('deviceType', '06'),
        ('mhtSignType', 'MD5'),
    ]
    trade_str = ipaynow_encrypt(encrypt_params, origin_params, APPKEY)
    return {'url': trade_str}


def generate_sign(parameter, app_key):
    h = hashlib.md5()
    h.update(app_key)
    app_key_hash = h.hexdigest()
    s = ''
    for k in sorted(parameter.keys()):
        s += '%s=%s&' % (k, parameter[k])
    s += 'key=%s' % app_key_hash
    m = hashlib.md5()
    m.update(s.encode('utf8'))
    sign = m.hexdigest().upper()
    return sign


def check_notify_sign(request):
    _LOGGER.info('receive ipaynow notify')
    raw_str = request.body.decode('utf-8')
    d = dict(urlparse.parse_qsl(raw_str))
    sign = d.pop('signature')
    d.pop('signType')
    if generate_sign(d, APPKEY) != sign:
        raise ParamError('ipaynow sign error: %s' % raw_str)
    pay_id = d['mhtOrderNo']
    trade_no = d.get('nowPayOrderNo')
    total_fee = float(d.get('mhtOrderAmt')) / 100
    trade_status = d.get('tradeStatus')
    pay = get_pay(pay_id)
    user_id = pay.user_id
    if not pay or pay.status != PAY_STATUS.SUBMIT:
        raise ParamError('pay %s has been processed' % pay_id)

    extend = {
        'title': u'充值-现在支付',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    if trade_status == 'A001':
        _LOGGER.info('ipaynow check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                       'price': total_fee,
                       'channel': 'ipaynow'})
        if res:
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay_id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('ipaynow response data show transaction failed, pay_id: %s', pay_id)


if __name__ == '__main__':
    encrypt_params = [
        ('mhtOrderType', '01'),
        ('mhtCurrencyType', '156'),
        ('mhtOrderDetail', 'Buydiskspace'),
        ('mhtOrderTimeOut', 120),
        ('mhtCharset', 'UTF-8'),
        ('mhtOrderName', "Buydiskspace"),
    ]
    origin_params = [
        ('funcode', 'WP001'),
        ('deviceType', '06'),
        ('mhtSignType', 'MD5'),
    ]
    trade_str = ipaynow_encrypt(encrypt_params, origin_params, APPKEY)
    print(trade_str)
