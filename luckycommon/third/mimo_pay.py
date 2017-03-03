# -*- coding: utf-8 -*-
import hashlib
import logging

from django.conf import settings

from luckycommon.async.async_job import track_one
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')
_SECRET_KEY = 'l549vhh7zh2skrs'

_EXCHANGE_RATIO = settings.EXCHANGE_RATIO


def _sign(key):
    return hashlib.md5(key).hexdigest()


def mimo_check_notify(request):
    trade_no = request.GET.get('mimotransid')
    pay_id = request.GET.get('transid')
    trade_status = request.GET.get('retcode')
    price = request.GET.get('rvalue')
    check_sum = request.GET.get('sig')
    servicename = request.GET.get('servicename')
    pay = get_pay(pay_id)
    currency = 'IDR'
    calculated_sign = _sign("servicename=%stransid=%smimotransid=%sretcode=%s%s" % (
        servicename, pay_id, trade_no, trade_status, _SECRET_KEY))
    _LOGGER.info("Coda Pay sign: %s, calculated sign: %",
                 check_sum, calculated_sign)
    if check_sum != calculated_sign:
        raise ParamError('sign not pass, data: %s' % request.GET)

    user_id = pay.user_id
    if not pay or pay.status != PayStatus.SUBMIT.value:
        raise ParamError('pay %s has been processed' % pay_id)

    total_fee = float(price) / _EXCHANGE_RATIO
    extend = {
        'title': u'deposit-MIMOPay',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    if int(trade_status) == 50000:
        _LOGGER.info('MIMO Pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
            user_id, pay_id, total_fee, currency))
        track_one.delay('recharge', {'price': float(total_fee), 'channel': 'mimo'}, user_id)
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'mimo'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception(
                    'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('MIMO Pay response data show transaction failed, data: %s', request.GET)
