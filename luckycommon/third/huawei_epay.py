# -*- coding: utf-8 -*-
import logging
import datetime, random, string, requests
import hmac, hashlib, json, base64

from django.conf import settings
from django.http import HttpResponse

from luckycommon.async.async_job import track_one
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError, DataError

_EXCHANGE_RATIO = settings.EXCHANGE_RATIO
_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_HUAWEIEPAY_KEY = '115cffec94ca4d4299b21310b7950535'
_HUAWEIEPAY_SECRET = "0b3e29ef7d47cb9c"
_HUAWEIEPAY_NOTIFIY_URL = "http://54.169.136.207/api/v1/pay/huawei_epay/notify/"

_HUAWEI_EPAY_ADD_TAX_TOTAL = 1100.00

_HUAWEI_API_HOST = "api-sp.digitalincloud.com"
_HUAWEI_PATH = {
    "query_channel": "/payment/queryChannel/v1",
    "creat_payment": "/payment/create/v1",
    "gen_auth_code": "/payment/generatePaymentAuthenticode/v1",
    "do_payment": "/payment/doPayment/v1"
}


def _sign():
    nonce_str = "".join(random.sample(string.ascii_letters + string.digits, 32)).lower()
    created_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    str_info = nonce_str + created_str + _HUAWEIEPAY_SECRET
    str = hashlib.sha256(str_info).digest()
    m = base64.b64encode(str)
    return [_HUAWEIEPAY_KEY, m, nonce_str, created_str]


def _generate_req_id(str_len=32):
    return "".join(random.sample(string.ascii_letters + string.digits, str_len))


def _sign_request_body(body_info, req_id):
    key_info = "%s&%s&%s" % (_HUAWEIEPAY_KEY, _HUAWEIEPAY_SECRET, req_id)
    message = ""
    if isinstance(body_info, dict):
        message = json.dumps(body_info)
    if isinstance(body_info, str):
        message = body_info
    code = hmac.new(key_info, message, digestmod=hashlib.sha256).digest()
    _LOGGER.error("body_sign body %s, req_id %s, sign %s" % (message, req_id, base64.b64encode(code)))
    return base64.b64encode(code)


def _sign_response_body(body_info):
    key_info = "%s&%s" % (_HUAWEIEPAY_KEY, _HUAWEIEPAY_SECRET)
    message = json.dumps(body_info)
    if isinstance(body_info, dict):
        message = json.dumps(body_info)
    if isinstance(body_info, str):
        message = body_info
    code = hmac.new(key_info, message, digestmod=hashlib.sha256).digest()
    return base64.b64encode(code)


_payment_data_temp = u"""{
"payer":{"payment_method": "phone_account",
"phone_account": {
"country": "ID",
"carrier": "%s",
"number": "%s"}
},
"transactions":[{
"amount": {
"total": "%s",
"currency": "%s"
},
"items": [
{
"id": "item-1234",
"name": "coin for happy lucky",
"description": "good lucky"
}
],
"outTradeNo": "%s",
"appInfo": {
"id": "APP000",
"name": "test app"
},
"description": "This is the payment transaction description."
}],
"callbacks": {
"notify_url": "http://54.169.136.207/api/v1/pay/huawei_epay/notify/",
},
"accesschannel": {
"access_channel": "1",
},
"extensionInfo":[
{
"key": "appdeveloper",
"value": "jack"
},
{
"key": "appversion",
"value": "1.00"
}]
}"""


def set_payment_data(carrier_id=36001, phone="666666", price=1100, currency="IDR", payid="123456789"):
    body_str = _payment_data_temp % (carrier_id, phone, price, currency, payid)
    body_dict = eval(body_str)
    return body_dict


def get_response_(body_data, url, method="POST"):
    username, passworddigiest, nonce, created = _sign()
    request_id = _generate_req_id()
    body_sign = _sign_request_body(body_data, request_id)
    headers = {
        'Authorization': 'WSSE realm="SDP", profile="UsernameToken", type="Appkey"',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-WSSE': 'UsernameToken Username="%s", PasswordDigest="%s", Nonce="%s", Created="%s"' % (
        username, passworddigiest, nonce, created),
        'Request-Id': request_id,
        'Body-Sign': 'sign_type="HMAC-SHA256", signature="%s"' % body_sign
    }
    _LOGGER.error("huwei_request_head %s" % headers)
    if method == "GET":
        headers.pop("Body-Sign")
        headers.pop("Request-Id")
        response = requests.get(url, headers=headers, allow_redirects=False, timeout=5.0)
        return response
    try:
        return requests.post(url, data=json.dumps(body_data), headers=headers, allow_redirects=False, timeout=5.0)
    except requests.exceptions.Timeout:
        _LOGGER.info("#HUAWEI PAY# requset %s connect time out, body %s" % (url, body_data))
    except Exception, e:
        _LOGGER.info(
            "#HUAWEI PAY# requset %s , %s in %s request with body %s" % (e.__class__.__name__, e, url, body_data))
    return None


def _get_haeder_for_ack(body_data):
    body_sign = _sign_response_body(body_data)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Body-Sign': 'sign_type="HMAC-SHA256", signature="%s"' % body_sign
    }
    return headers


_CARRIER_PREFIX = {
    '0812': 'TEL',
    '0813': 'TEL',
    '0821': 'TEL',
    '0822': 'TEL',
    '0823': 'TEL',
    '0851': 'TEL',
    '0852': 'TEL',
    '0853': 'TEL',
    '0814': 'IR',
    '0815': 'IR',
    '0816': 'IR',
    '0855': 'IR',
    '0856': 'IR',
    '0857': 'IR',
    '0858': 'IR',
    '0817': 'XL',
    '0818': 'XL',
    '0819': 'XL',
    '0831': 'XL',
    '0832': 'XL',
    '0834': 'XL',
    '0838': 'XL',
    '0859': 'XL',
    '0877': 'XL',
    '0878': 'XL',
    '0895': 'TRI',
    '0896': 'TRI',
    '0897': 'TRI',
    '0898': 'TRI',
    '0899': 'TRI',
    '0881': 'SF',
    '0882': 'SF',
    '0883': 'SF',
    '0884': 'SF',
    '0885': 'SF',
    '0886': 'SF',
    '0887': 'SF',
    '0888': 'SF',
    '0889': 'SF',
}


def pre_process_indonesia_phone(phone):
    if phone.startswith("08"):
        return phone[1:]
    elif phone.startswith("8"):
        return phone
    elif phone.startswith("628"):
        return phone[2:]
    elif phone.startswith("620"):
        return phone[3:]


def get_carrier_from_phone(phone):
    if phone.startswith("8"):
        start_num = "0" + phone[:3]
        carrier_code = _CARRIER_PREFIX.get(start_num, "")
        return {"XL": 36001, "IR": 36002, "TEL": 36003, "h3i": 36004}.get(carrier_code, 0)
    else:
        return 0


def _check_sign(body_info={}, req_id="", str_info=""):
    if _sign_request_body(body_info, req_id) == str_info:
        return True
    else:
        return False


callback_success_ack_body = {"result": {"code": "000000", "message": "Success"}}
callback_success_header = _get_haeder_for_ack(callback_success_ack_body)
callback_failure_ack_body = {"result": {"code": "E000000", "message": "System error"}}
callback_failure_header = _get_haeder_for_ack(callback_failure_ack_body)


def huaweipay_check_notify(request):
    body_dict = json.loads(request.body)
    sign_info = request.META.get('HTTP_BODY_SIGN')
    sign = sign_info.split(", ")[-1].split("signature=")[-1][1:-1]
    _LOGGER.error('##* Huawei pay *## callback req_sign info %s' % sign_info)
    _LOGGER.error('##* Huawei pay *## callback req_sign type %s, info %s' % (type(sign), sign))
    req_id = request.META.get('HTTP_REQUEST_ID')
    _LOGGER.error('##* Huawei pay *## callback req_id info %s' % req_id)
    if not _check_sign(body_info=request.body, req_id=req_id, str_info=sign):
        return HttpResponse(status=500)
    payment = body_dict["payment"]
    _LOGGER.error('##* Huawei pay *## payment info %s' % payment)
    transaction = payment["transactions"][0]
    pay_id = transaction.get("outTradeNo", 0)
    price = transaction["amount"]["total"]
    _LOGGER.error('##* Huawei pay *## callbck value pay_id %s, pay price %s' % (pay_id, price))
    currency = transaction["amount"]['currency']
    callback_status = payment.get('state')
    status = {"created": 0, "pending": 1, "completed": 2, "failed": 4, "canceled": 8}.get(callback_status, 1)
    trade_no = payment.get("id")
    pay_id = int(pay_id)
    pay = get_pay(pay_id)
    user_id = pay.user_id
    if not pay or (pay.status != PayStatus.SUBMIT.value and pay.status != PayStatus.FAIL.value):
        raise ParamError('pay %s has been processed' % pay_id)

    total_fee = float(price) / _HUAWEI_EPAY_ADD_TAX_TOTAL
    extend = {
        'title': u'deposit-HuaweiPay',
        'ext': {
            'trade_status': status,
            'trade_no': trade_no,
            'total_fee': total_fee
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    if callback_status == "completed":
        _LOGGER.error('Huawei pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
            user_id, pay_id, total_fee, currency))
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        if res:
            track_one.delay('recharge', {'price': float(total_fee), 'channel': 'huawei'}, user_id)
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'huaweipay'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception(
                    'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
    else:
        add_pay_fail_transaction(user_id, pay_id, total_fee, extend)


def huawei_check_payment():
    pass
