# -*- coding: utf-8 -*-
import hashlib
import logging
import urllib

from django.conf import settings

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_API_KEY = 'ef5dfd28f0527d32'
_EXCHANGE_RATIO = settings.EXCHANGE_RATIO
_SECRET = 'ef0a9e3f2b67af4bcaf557f93c404c3c'

def _sign(pm_id, amount, order_id, state):
    s = '|'.join([_API_KEY, pm_id, amount, 'IDR', order_id, state, _SECRET])
    
    sign = hashlib.md5(s).hexdigest()
    return sign


def payssion_check_notify(request):
    data = dict(request.POST.iteritems())
    _LOGGER.debug("Payssion Pay notify data: %s", data)

    trade_no = data.get('transaction_id')
    pay_id = long(data.get('order_id'))
    trade_status = data.get('state')
    total_fee = data.get('amount')
    sign = data.get('notify_sig')
    pm_id = data.get('pm_id')
    calculated_sign = _sign(pm_id, str(total_fee), str(pay_id), trade_status)
    if sign != calculated_sign:
        raise ParamError('sign not pass, data: %s, sign: %s, calculated sign: %s' % (request.POST, sign, calculated_sign))

    total_fee = float(total_fee) / _EXCHANGE_RATIO
    pay = get_pay(pay_id)
    _LOGGER.error('payssion pay check id is %s', pay_id)
    user_id = pay.user_id
    if not pay or pay.status != PayStatus.SUBMIT.value:
        raise ParamError('pay %s has been processed' % pay_id)

    extend = {
        'title': u'deposit-Payssion',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    if str(trade_status) == 'completed':
        _LOGGER.info('Payssion Pay check order success, user_id:%s pay_id:%s, amount: %s' % (user_id, str(pay_id), total_fee))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'payssion'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('Payssion response data show transaction failed, data: %s', request.POST)
