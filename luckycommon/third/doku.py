# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from hashlib import sha1

from luckycommon.async.async_job import track_one
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_fail_transaction
from luckycommon.db.transaction import add_pay_success_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError

_EXCHANGE_RATIO = 1000
_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

# doku test credit card. 4111 - 1111 - 1111 - 1111, 04/20, 869, phone: 0217998391

ORDER_URL = 'http://staging.doku.com/Suite/Receive'
MALL_ID = '3798'
SHARED_KEY = 'C1F2OqSy22az'


def _sign(pay_amount, pay_id):
    signature = sha1(str(pay_amount) + MALL_ID + SHARED_KEY + str(pay_id)).hexdigest()
    return signature


def _notify_sign(pay_amount, pay_id, result_msg, verify_status):
    signature = sha1(str(pay_amount) + MALL_ID + SHARED_KEY + str(pay_id) + result_msg + verify_status).hexdigest()
    return signature


def doku_create_charge(pay, pay_amount):
    pay_id = str(pay.id)
    pay_amount = str(int(pay_amount) * _EXCHANGE_RATIO) + '.00'
    signature = _sign(pay_amount, pay_id)
    _LOGGER.info("pay_id: %s, pay_amount: %s, signature: %s" % (pay_id, pay_amount, signature))
    response = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DOKU Pay</title>
</head>
<body>

<form id='pay_form' action="%s" method="POST">
    <input name="MALLID" type="hidden" value="%s">
    <input name="BASKET" type="hidden" value="testing item,%s,1,%s">
    <input name="CHAINMERCHANT" type="hidden" value="NA">
    <input name="AMOUNT" type="hidden" value="%s">
    <input name="PURCHASEAMOUNT" type="hidden" value="%s">
    <input name="TRANSIDMERCHANT" type="hidden" value="%s">
    <input name="WORDS" type="hidden" value="%s">
    <input name="CURRENCY" type="hidden" value="360">
    <input name="PURCHASECURRENCY" type="hidden" value="360">
    <input name="COUNTRY" type="hidden" value="ID">
    <input name="SESSIONID" type="hidden" value="fexCfZs72DFT5Gy0TQiF">
    <input name="REQUESTDATETIME" type="hidden" value="%s">
    <input name="NAME" type="hidden" value="CustomerName">
    <input name="EMAIL" type="hidden" value="customer@domain.com">
    <input name="PAYMENTCHANNEL" type="hidden" value="">
</form>

<script type="text/javascript">
document.getElementById('pay_form').submit();
</script>

</body>
</html>
       """ % (ORDER_URL, MALL_ID, pay_amount, pay_amount, pay_amount, pay_amount, pay_id, signature, datetime.now().strftime("%Y%m%d%H%M%S"))
    return response


def doku_check_notify(request):
    trade_no = request.POST.get('APPROVALCODE')
    pay_id = request.POST.get('TRANSIDMERCHANT')
    trade_status = request.POST.get('RESPONSECODE')
    pay_amount = request.POST.get('AMOUNT')
    signature = request.POST.get('WORDS')
    result_msg = request.POST.get('RESULTMSG')
    verify_status = request.POST.get('VERIFYSTATUS')
    pay = get_pay(pay_id)
    currency = 'IDR'
    calculated_sign = _notify_sign(pay_amount, pay_id, result_msg, verify_status)
    _LOGGER.info("pay_id: %s, pay_amount: %s, signature: %s" % (pay_id, pay_amount, signature))
    if signature != calculated_sign:
        raise ParamError("doku check signature failed. sign: %s, calculated sign: %s" % (signature, calculated_sign))

    user_id = pay.user_id
    if not pay or pay.status != PayStatus.SUBMIT.value:
        raise ParamError('pay %s has been processed' % pay_id)

    total_fee = float(pay_amount) / _EXCHANGE_RATIO
    extend = {
        'title': u'deposit-doku',
        'ext': {
            'trade_status': trade_status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    if trade_status == '0000':
        _LOGGER.info('Doku Pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
            user_id, pay_id, total_fee, currency))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            track_one.delay('recharge', {'price': float(total_fee), 'channel': 'doku'}, user_id)
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'doku'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception(
                    'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
        _LOGGER.error('Doku Pay response data show transaction failed, data: %s', request.POST)

