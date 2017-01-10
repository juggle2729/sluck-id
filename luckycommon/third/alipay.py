# -*- coding: utf-8 -*-
import os
import rsa
import json
import base64
import urllib
import logging
import requests

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import (add_pay_wait_transaction,
                                        add_pay_success_transaction,
                                        add_pay_fail_transaction)
from luckycommon.model.pay import (PAY_TYPE, PAY_STATUS,
                                   PINGXX_CHANNELS_TO_NAMES)
from luckycommon.pay.handler import pay_after_recharge

from luckycommon.utils.exceptions import ParamError, AuthenticateError

from django.conf import settings
from django.utils.encoding import smart_unicode


_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_PARTNER_ID = '2088121334251002'
_SELLER_ID = '2088121334251002'
_DEFAULT_SUBJECT = u'deposit'
_DEFAULT_BODY = u'deposit content'
_SERVICE_URL = 'mobile.securitypay.pay'
_INPUT_CHARSET = 'utf-8'
_HTTPS_VERIFY_URL = 'https://mapi.alipay.com/gateway.do?service=notify_verify&'
_ALIPAY_NOTIFY_URL = settings.ROOT_URL + '/api/v1/pay/alipay/notify/'

_NOTIFY_STATUS = {
    "WAIT": "WAIT_BUYER_PAY",
    "CLOSED": "TRADE_CLOSED",
    "SUCCESS": "TRADE_SUCCESS",
    "FINISHED": "TRADE_FINISHED"
}

_private_rsa_key = None
_public_rsa_key_ali = None

path = os.path.dirname(__file__)
priv_path = os.path.abspath(os.path.join(path, "rsa_private_key.pem"))
pub_path_ali = os.path.abspath(os.path.join(path, "rsa_public_key_ali.pem"))

pem = open(priv_path, "r").read()
_private_rsa_key = rsa.PrivateKey.load_pkcs1(pem)

pem = open(pub_path_ali, "r").read()
_public_rsa_key_ali = rsa.PublicKey.load_pkcs1_openssl_pem(pem)


def sign(content):
    content = content.encode(_INPUT_CHARSET)
    sign = rsa.sign(content, _private_rsa_key, "SHA-1")
    sign = base64.encodestring(sign).replace("\n", "")
    return sign


def alipay_send_order(pay, pay_amount):
    if not pay or pay.status != PAY_STATUS.SUBMIT\
            or pay.pay_type != PAY_TYPE.ALIPAY:
        raise AuthenticateError('pay id invalid')

    if float(pay_amount) <= 0:
        raise ParamError('pay amount invalid')

    pay_id = pay.id
    notify_url = _ALIPAY_NOTIFY_URL
    # create order info
    _ORDER_INFO_PARAMS = (('partner', _PARTNER_ID),
                          ('seller_id', _SELLER_ID),
                          ('out_trade_no', pay_id),
                          ('subject', _DEFAULT_SUBJECT),
                          ('body', _DEFAULT_BODY),
                          ('total_fee', pay_amount),
                          ('notify_url', notify_url),
                          ('service', _SERVICE_URL),
                          ('payment_type', '1'),
                          ('_input_charset', _INPUT_CHARSET),
                          ('it_b_pay', '30m'))

    order_info = ""
    for param in _ORDER_INFO_PARAMS:
        k, v = param[0], param[1]
        order_info += '%s="%s"&' % (k, v)
    order_info = order_info[:-1]

    signed_str = sign(order_info)
    urllib.quote(signed_str)
    pay_info = '%s&sign="%s"&sign_type="RSA"' % (order_info, signed_str)
    # add wait transaction
    # extend = {
    #    'title': u'充值-支付宝',
    #    'ext': {
    #        'trade_status': _NOTIFY_STATUS['WAIT'],
    #        'trade_no': None,
    #        'total_fee': pay_amount
    #    }
    # }
    # add_pay_wait_transaction(pay.user_id, pay_id, pay_amount, extend)

    return pay_info


def alipay_check_notify(notify_id):
    verify_url = _HTTPS_VERIFY_URL + \
        "partner=%s&notify_id=%s" % (_PARTNER_ID, notify_id)
    try:
        r = requests.get(verify_url)
        return r.text
    except Exception as e:
        _LOGGER.error('verfiy notify id request error.(%s)' % e)
        return None


def decode_base64(data):
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += b'=' * missing_padding
    return base64.decodestring(data)

pubkey = RSA.importKey(open(os.path.abspath(
    os.path.join(path, "pingpp.pub"))).read())


def verify(signature, original_data):
    signs = decode_base64(signature)
    data = original_data.encode('utf-8')
    digest = SHA256.new(data)
    pkcs = PKCS1_v1_5.new(pubkey)
    return pkcs.verify(digest, signs)


def check_notify_sign(request):
    signature = request.META.get('HTTP_X_PINGPLUSPLUS_SIGNATURE')
    try:
        request_body = smart_unicode(request.body)
    except Exception as e:
        request_body = str(request.body)

    isSign = verify(signature, request_body)
    request_json = json.loads(request_body)
    notify_dict = request_json['data']['object']
    event_id = request_json['id']
    trade_status = request_json['type']
    pingxx_id = notify_dict.get('id')
    pay_id = notify_dict.get('order_no')
    _LOGGER.info("check_notify_sign, pingxx_id:%s, pay_id: %s, trade_status:%s, isSign: %s",
                 pingxx_id, pay_id, trade_status, isSign)
    if isSign:
        if not pay_id:
            _LOGGER.error("fatal error, out_trade_no not exists, notify_id:%s",
                          event_id)
            raise ParamError('Pingpp event does not contain pay ID')

        pay = get_pay(pay_id)
        if not pay or pay.status != PAY_STATUS.SUBMIT:
            raise ParamError(
                'pay %s has been processed, pay: %s' % (pay_id, pay))

        user_id = pay.user_id
        trade_no = notify_dict['transaction_no']
        total_fee = notify_dict['amount']
        total_fee = float(total_fee) / 100
        channel = PINGXX_CHANNELS_TO_NAMES[notify_dict['channel']]

        extend = {
            'title': u"充值-%s" % channel,
            'ext': {
                'trade_status': trade_status,
                'trade_no': trade_no,
                'total_fee': total_fee
            }
        }

        update_pay_ext(pay_id, extend['ext'])
        if trade_status == 'charge.succeeded':
            _LOGGER.info('pingpp check order success, user_id:%s pay_id:%s',
                         user_id, pay_id)
            res = add_pay_success_transaction(
                user_id, pay_id, total_fee, extend)
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'ping++'})
            if res:
                try:
                    pay_after_recharge(pay)
                except Exception as e:
                    _LOGGER.exception(
                        'pay_after_recharge of pay[%s] exception.(%s)',
                        pay.id, e)
        else:
            add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
            _LOGGER.error(
                'Pingpp event type should be succeeded, event ID: %s',
                event_id)
    else:
        _LOGGER.error(
            'Pingpp header signature not verified, event ID: %s', event_id)
