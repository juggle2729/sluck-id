# -*- coding: utf-8 -*-
import requests
import json
import logging
import hashlib
import datetime

#from django.conf import settings
#from luckycommon.db.pay import get_pay, update_pay_ext
#from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
#from luckycommon.model.pay import PayStatus
#from luckycommon.pay.handler import pay_after_recharge
#from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

ORDER_URL = 'http://dev.indomog.com/indomog2/new_core/index.php/paywall/main'
#API_KEY_DICT = settings.INDOMOG_API_KEY_DICT

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


def indomog_create_charge(pay, pay_amount, currency):
    #price = pay_amount / settings.SUPPORT_CURRENCIES[currency]['exchange_rate']
    price = pay_amount
    payload = {"RMID": '0910403545',
               "QID": pay['id'],
               "RC": 4200,
               "Alg": "ts",
               "AlgID": "hello244@mailinator.com",
               "Name" :"Test Aja",
               "EmailHP" :"hello244@mailinator.com",
               "IPD" :"127.0.0.1",
               "Now" :str(datetime.datetime.utcnow())[:19],
               "QUrlBackground" :"http://testaja.qhios.com/a.jpg",
               "QUrlImage" :"http://testaja.qhios.com/b.jpg",
               "QUrlLogo" :"http://testaja.qhios.com/c.jpg",
               "QUrlSuccess" :"http://id.lucky-gou.com/api/v1/pay/indomog/notify/%s/" % pay['id'],
               "QUrlPending" :"http://testaja.qhios.com/pending",
               "QUrlCancel" :"http://testaja.qhios.com/cancel",
               "PurchaseAmt" :str(price),
               "PurchaseDesc" :"payment for Toko Seribu",
               "BMod" :"BCATRF, MANTRF, BPVTRF, BIITRF, BRITRF, BNITRF, BSMTRF, MOGACC, MOGVCH, KLKBCA, KPYBCA, SMSMAN, INTMAN, CC",
    }
    signature = hashlib.sha1(str(payload['RMID'])+str(payload['QID'])+str(payload['RC'])+str(payload['Alg'])+str(payload['AlgID'])+str(payload['Name'])+str(payload['EmailHP'])+str(payload['IPD'])+str(payload['Now'])+str(payload['QUrlBackground'])+str(payload['QUrlImage'])+str(payload['QUrlLogo'])+str(payload['QUrlSuccess'])+str(payload['QUrlPending'])+str(payload['QUrlCancel'])+str(payload['PurchaseAmt'])+str(payload['PurchaseDesc'])+str(payload['BMod'])+'123456').hexdigest()
    payload.update({'Signature':signature})

    _LOGGER.info("post data: %s" % payload)
    response = requests.post(ORDER_URL,
                             data=payload)
    print response.content
    #if response.status_code == 200 and response_dict['initResult']['resultCode'] == 0:
    #    return settings.CODA_PAY_GATEWAY_URL % response_dict['initResult']['txnId']
    #else:
    #    _LOGGER.error("response data: %s" % response_dict)
    #    return None


#
#
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
    pay=  {'id': 77077}
    indomog_create_charge(pay, 66, None)
