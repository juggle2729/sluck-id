# -*- coding: utf-8 -*-
# pip install paypal
from paypal.interface import PayPalInterface

import logging
from django.conf import settings

from luckycommon.credit.db.credit import add_special_recharge_award_credit
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

# exchange ratio just for SGD
_EXCHANGE_RATIO = 0.1
_CURRENCY = 'SGD'
_AWARD_CREDIT_UNIT = 10

PAYPAL_REDIRECT_URL = settings.PAYPAL_REDIRECT_URL


def paypal_create_charge(pay, pay_amount, return_url=settings.PAYPAL_NOTIFY_URL,
                         cancel_url=settings.PAYPAL_CANCEL_URL):
    paypal = PayPalInterface(API_USERNAME=settings.PAYPAL_API_USERNAME,
                             API_PASSWORD=settings.PAYPAL_API_PASSWORD,
                             API_SIGNATURE=settings.PAYPAL_API_SIGNATURE,
                             API_ENVIRONMENT=settings.PAYPAL_API_ENVIRONMENT)
    set_result = paypal.set_express_checkout(
        PAYMENTREQUEST_0_AMT=pay_amount * _EXCHANGE_RATIO,
        PAYMENTREQUEST_0_CURRENCYCODE=_CURRENCY,
        PAYMENTREQUEST_0_PAYMENTACTION="Sale",
        PAYMENTREQUEST_0_INVNUM=str(pay.id),
        RETURNURL=return_url,
        CANCELURL=cancel_url
    )
    token = set_result["TOKEN"]
    redirect_url = PAYPAL_REDIRECT_URL % token
    _LOGGER.info("paypal redirect url: %s" % redirect_url)
    return redirect_url


def paypal_do_charge(token):
    paypal = PayPalInterface(API_USERNAME=settings.PAYPAL_API_USERNAME,
                             API_PASSWORD=settings.PAYPAL_API_PASSWORD,
                             API_SIGNATURE=settings.PAYPAL_API_SIGNATURE,
                             API_ENVIRONMENT=settings.PAYPAL_API_ENVIRONMENT)
    detail_result = paypal.get_express_checkout_details(TOKEN=token)
    _LOGGER.info("paypal checkout detail: %s" % detail_result)
    currency = detail_result['CURRENCYCODE']
    confirm_result = paypal.do_express_checkout_payment(TOKEN=detail_result['TOKEN'],
                                                        PAYMENTACTION="Sale",
                                                        PAYERID=detail_result['PAYERID'],
                                                        CURRENCYCODE=currency,
                                                        AMT=detail_result['AMT'])
    _LOGGER.info("paypal checkout confirm result: %s" % confirm_result)
    trade_status = confirm_result['PAYMENTSTATUS']
    total_fee = float(confirm_result['AMT']) / _EXCHANGE_RATIO
    pay_id = detail_result['PAYMENTREQUEST_0_INVNUM']
    trade_no = confirm_result['PAYMENTINFO_0_TRANSACTIONID']
    _LOGGER.info("paypal checkout confirm result: %s" % confirm_result)
    _LOGGER.info("amount: %s, currency: %s, pay_id: %s" % (total_fee, currency, pay_id))
    pay = get_pay(pay_id)
    user_id = pay.user_id
    if not pay or pay.status != PayStatus.SUBMIT.value:
        raise ParamError('pay %s has been processed' % pay_id)

    extend = {
        'title': u'deposit-Paypal',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }

    update_pay_ext(pay_id, extend['ext'])

    if trade_status == 'Completed' or (trade_status == 'Pending' and confirm_result['PENDINGREASON'] == 'multicurrency'):
        _LOGGER.info('paypal check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        add_special_recharge_award_credit(user_id, total_fee * _AWARD_CREDIT_UNIT)
        if res:
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'paypal'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('paypal response data show transaction failed, data: %s', confirm_result)


if __name__ == '__main__':
    # paypal_create_charge(None, None, "USD", "http://return.com", "http://cancel.com")
    paypal_do_charge("EC-6F260795CS776210N")
