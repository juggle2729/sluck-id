# -*- coding: utf-8 -*-
import json
import hashlib
import logging
import requests

from django.conf import settings

from luckycommon.async.async_job import track_one
from luckycommon.credit.db.credit import add_special_recharge_award_credit
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError, DataError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')
_EXCHANGE_RATIO = settings.EXCHANGE_RATIO


def mimo_create_charge(pay, pay_amount, currency, pay_method='atm'):
    if pay_amount <= 1:
        raise DataError('Pay amount must be bigger than 1')
    if pay_method not in settings.MIMOPAY_PAYMENT_METHODS:
        raise DataError('Invalid mimo pay method')

    pay_id = str(pay.id)
    request_params = {
        'host': settings.MIMOPAY_API_HOST,
        'method': settings.MIMOPAY_PAYMENT_METHODS[pay_method],
        'user_id': pay.user_id,
        'product_name': settings.MIMOPAY_PRODUCT_NAMES[pay_method],
        'merchant_code': settings.MIMOPAY_MERCHANT_CODES[pay_method],
        'tid': pay_id,
        'currency_code': currency,
        'amount': int(pay_amount) * _EXCHANGE_RATIO,
        'key': _sign(pay_id + settings.MIMOPAY_MERCHANT_CODES[pay_method] + settings.MIMOPAY_SECRET_KEYS[pay_method]),
    }

    url = '%(host)s/%(method)s/load/%(user_id)s/%(product_name)s/%(merchant_code)s/' \
          '%(tid)s/%(currency_code)s/%(amount)s/%(key)s' % request_params
    return url


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
        servicename, pay_id, trade_no, trade_status, settings.MIMOPAY_SECRET_KEYS['atm']))
    _LOGGER.info("Mimo atm Pay sign: %s, calculated sign: %", check_sum, calculated_sign)
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
        _LOGGER.info('MIMO atm Pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
            user_id, pay_id, total_fee, currency))
        track_one.delay('recharge', {'price': float(total_fee), 'channel': 'mimo'}, user_id)
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge', 'price': total_fee, 'channel': 'mimo'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('MIMO atm Pay response data show transaction failed, data: %s', request.GET)


def bubble_mimo_check_notify(request):
    """ mimopay telkomsel callback: use for bubble and lucky """
    trade_no = request.GET.get('mimotransid')
    pay_id = request.GET.get('transid')
    trade_status = request.GET.get('retcode')
    price = request.GET.get('rvalue')
    check_sum = request.GET.get('sig')
    servicename = request.GET.get('servicename')
    currency = 'IDR'
    calculated_sign = _sign("servicename=%stransid=%smimotransid=%sretcode=%s%s" % (
        servicename, pay_id, trade_no, trade_status, settings.MIMOPAY_SECRET_KEYS['telkomsel']))
    _LOGGER.info("MIMO telkomsel Pay sign: %s, calculated sign: %", check_sum, calculated_sign)
    if check_sum != calculated_sign:
        raise ParamError('sign not pass, data: %s' % request.GET)

    total_fee = float(price) / _EXCHANGE_RATIO

    if str(pay_id).startswith('Bubble_'):  # bubble
        if int(trade_status) == 50000:
            _LOGGER.info('Bubble MIMO Pay check order success, pay_id:%s, amount: %s, currency: %s' % (
                pay_id, total_fee, currency))
            _TRACKER.info({
                'trade_status': trade_status,
                'trade_no': trade_no,
                'pay_id': pay_id,
                'price': price,
                'total_fee': total_fee,
                'check_sum': check_sum,
                'servicename': servicename,
            })
        else:
            _LOGGER.error('Bubble MIMO Pay response data show transaction failed, data: %s', request.GET)
    else:  # lucky
        pay = get_pay(pay_id)
        user_id = pay.user_id
        if not pay or pay.status != PayStatus.SUBMIT.value:
            raise ParamError('pay %s has been processed' % pay_id)

        extend = {
            'title': u'deposit-MIMOPay-telkomsel',
            'ext': {
                'trade_status': trade_status,
                'trade_no': trade_no,
                'total_fee': total_fee
            }
        }
        update_pay_ext(pay_id, extend['ext'])
        if int(trade_status) == 50000:
            _LOGGER.info('MIMO telkomsel Pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
                user_id, pay_id, total_fee, currency))
            track_one.delay('recharge', {'price': float(total_fee), 'channel': 'mimo_telkomsel'}, user_id)
            res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
            if res:
                _TRACKER.info({'user_id': user_id, 'type': 'recharge', 'price': total_fee, 'channel': 'mimo_telkomsel'})
                try:
                    pay_after_recharge(pay)
                except Exception as e:
                    _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
        else:
            add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
            _LOGGER.error('MIMO telkomsel Pay response data show transaction failed, data: %s', request.GET)
