# -*- coding: utf-8 -*-
import requests
import json
from random import randint
import logging
from hashlib import sha1

#from django.conf import settings
#from luckycommon.db.pay import get_pay, update_pay_ext
#from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
#from luckycommon.model.pay import PayStatus
#from luckycommon.pay.handler import pay_after_recharge
#from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

ORDER_URL = 'http://staging.doku.com/Suite/Receive'
#API_KEY_DICT = settings.DOKU_API_KEY_DICT

COUNTRY_CODES = {
    'SGD': '702',
    'IDR': '360',
    'MYR': '458',
    'THB': '764',
    'PHP': '608',
    'VND': '704',
    'TWD': '158',
    'LKR': '144',
}

CURRENCY_CODES = {
    'SGD': '702',
    'IDR': '360',
    'MYR': '458',
    'THB': '764',
    'PHP': '608',
    'VND': '704',
    'TWD': '901',
    'LKR': '144',
}

API_KEY_DICT = {'mallid': '3798', 'shared_key':'NB5aG16q4Zip'}

def doku_create_charge(pay, pay_amount, currency, user_name='test', user_email='test@test.com'):
    trans = str(pay.id)
    pay_amount = str(pay_amount)
    w = sha1(str(pay_amount) + '3798NB5aG16q4Zip'+str(trans)).hexdigest()
    #s = """<form action="http://staging.doku.com/Suite/Receive" method="POST">
    #        <input name="MALLID" value="3798" >
    #            <input name="BASKET" value="testing item,10000.00,1,10000.00" >
    #                <input name="CHAINMERCHANT" type="hidden" value="NA" >
    #                    <input name="AMOUNT" value="%s" >
    #                    <input name="PURCHASEAMOUNT" type="hidden" value="%s" >
    #                    <input name="TRANSIDMERCHANT"  value="%s" >
    #                    <input name="WORDS" value="%s" >
    #                    <input name="CURRENCY" type="hidden" value="360" >
    #                    <input name="PURCHASECURRENCY" type="hidden" value="360" >
    #                    <input name="COUNTRY" value="ID" >
    #                    <input name="SESSIONID" type="hidden" value="234asdf234" >
    #                    <input name="REQUESTDATETIME" type="hidden" value="20151212000000" >
    #                    <input name="NAME" value="CustomerName" >
    #                    <input name="EMAIL" type="hidden" value="customer@domain.com">
    #                    <input name="PAYMENTCHANNEL" type="hidden" value="" >
    #                        <input type="submit" name="submit" value="Submit" />
    #                        </form>
    #                        """ % (pay_amount, pay_amount, trans, w)
    #w = sha1('75.003798NB5aG16q4Zip'+str(trans)).hexdigest()
    s = """<form action="http://staging.doku.com/Suite/Receive" method="POST">
            <input name="MALLID" value="3798" >
                <input name="BASKET" value="testing item,10000.00,1,10000.00" >
                    <input name="CHAINMERCHANT" type="hidden" value="NA" >
                        <input name="AMOUNT" value="%s" >
                        <input name="PURCHASEAMOUNT" type="hidden" value="%s" >
                        <input name="TRANSIDMERCHANT"  value="%s" >
                        <input name="WORDS" value="%s" >
                        <input name="CURRENCY" type="hidden" value="360" >
                        <input name="PURCHASECURRENCY" type="hidden" value="360" >
                        <input name="COUNTRY" value="ID" >
                        <input name="SESSIONID" type="hidden" value="234asdf234" >
                        <input name="REQUESTDATETIME" type="hidden" value="20151212000000" >
                        <input name="NAME" value="CustomerName" >
                        <input name="EMAIL" type="hidden" value="customer@domain.com">
                        <input name="PAYMENTCHANNEL" type="hidden" value="" >
                            <input type="submit" name="submit" value="Submit" />
                            </form>
                            """ % (pay_amount, pay_amount, trans, w)
    return s


#def _sign(origin_str):
#    m = hashlib.sha1(origin_str)
#    sign = m.hexdigest().lower()
#    return sign


#def coda_check_notify(request):
#    trade_no = request.GET.get('TxnId')
#    pay_id = request.GET.get('OrderId')
#    trade_status = request.GET.get('ResultCode')
#    price = request.GET.get('TotalPrice')
#    check_sum = request.GET.get('Checksum')
#    pay = get_pay(pay_id)
#    ext = json.loads(pay.extend)
#    currency = ext['currency']
#    calculated_sign = _sign("%s%s%s%s" % (
#        trade_no, API_KEY_DICT[currency], pay_id, trade_status))
#    _LOGGER.info("Coda Pay sign: %s, calculated sign: %",
#                 check_sum, calculated_sign)
#    if check_sum != calculated_sign:
#        raise ParamError('sign not pass, data: %s' % request.GET)
#
#    user_id = pay.user_id
#    if not pay or pay.status != PayStatus.SUBMIT.value:
#        raise ParamError('pay %s has been processed' % pay_id)
#
#    total_fee = float(price) * settings.SUPPORT_CURRENCIES[
#        currency]['exchange_rate']
#    extend = {
#        'title': u'deposit-CodaPay',
#        'ext': {
#            'trade_status': trade_status,
#            'trade_no': trade_no,
#            'total_fee': total_fee
#        }
#    }
#    update_pay_ext(pay_id, extend['ext'])
#    if int(trade_status) == 0:
#        _LOGGER.info('Coda Pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
#            user_id, pay_id, total_fee, currency))
#        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
#        if res:
#            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
#                           'price': total_fee,
#                           'channel': 'coda'})
#            try:
#                pay_after_recharge(pay)
#            except Exception as e:
#                _LOGGER.exception(
#                    'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
#    else:
#        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
#        _LOGGER.error('Coda Pay response data show transaction failed, data: %s', request.GET)
#

if __name__ == '__main__':
    pay = {'id': 'sndbox_' + str(randint(1000,13333))}
    doku_create_charge(pay, 66, 'IDR')
