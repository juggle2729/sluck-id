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

_SERVICE_ID = settings.FORTUMO_SERVICE_ID
_SECRET = settings.FORTUMO_SECRET
_GATEWAY = 'http://pay.fortumo.com/mobile_payments/%s?' % _SERVICE_ID


def fortumo_create_charge(pay, return_url):
    params = {
        'cuid': str(pay.id),
        'callback_url': return_url if return_url else settings.FORTUMO_CLOSE_URL,
    }
    sign = _sign(params)
    params['sig'] = sign
    query_str = urllib.urlencode(params)
    return _GATEWAY + query_str


def _sign(params):
    s = u''
    for k in sorted(params.keys()):
        s += u'%s=%s' % (k, params[k])
    s += _SECRET
    _LOGGER.debug("Fortumo sign: %s", s.encode('utf8'))
    m = hashlib.md5()
    m.update(s.encode('utf8'))
    sign = m.hexdigest()
    return sign


def fortumo_check_notify(request):
    data = dict(request.GET.iteritems())
    _LOGGER.debug("Fortumo Pay notify data: %s", data)

    trade_no = data.get('payment_id')
    pay_id = data.get('cuid')
    trade_status = data.get('status')
    total_fee = data.get('amount')
    sign = data.pop('sig')
    calculated_sign = _sign(data)
    if sign != calculated_sign:
        raise ParamError('sign not pass, data: %s, sign: %s, calculated sign: %s' % (request.GET, sign, calculated_sign))

    pay = get_pay(pay_id)
    user_id = pay.user_id
    if not pay or pay.status != PayStatus.SUBMIT.value:
        raise ParamError('pay %s has been processed' % pay_id)

    extend = {
        'title': u'deposit-Fortumo',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    if str(trade_status) == 'completed':
        _LOGGER.info('Fortumo Pay check order success, user_id:%s pay_id:%s, amount: %s' % (user_id, pay_id, total_fee))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'fortumo'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('Fortumo response data show transaction failed, data: %s', request.GET)
