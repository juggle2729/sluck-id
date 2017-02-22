# -*- coding: utf-8 -*-
import requests
import json
import logging
import hashlib
import  base64
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA


from django.conf import settings
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import ParamError
from luckycommon.cache.redis_cache import set_gwallet_purchase_token

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

API_KEY_DICT = settings.CODA_API_KEY_DICT

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

_EXCHANGE_RATIO = settings.EXCHANGE_RATIO
PRODUCT_ID = {
    '1koin' : 10*_EXCHANGE_RATIO,
    'koin2' : 20*_EXCHANGE_RATIO,
    'koin3' : 50*_EXCHANGE_RATIO,
    'koin4' : 100*_EXCHANGE_RATIO,
    'koin5' : 200*_EXCHANGE_RATIO,
}

pubKey = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApl2HZzIJwax5ui/CXW50D2x590hikmBIiE6G7XPkzsi5mBVNQTH0lcpyAzg8DECCXznFN9duhSVdfs3kyuJdl9jYtCUb9aYNtKCAKatGQqK2dgpxdtx6QwVPApa7XXOGmeAAVq6WAgVVU7QzYuqCRMk15fDj7+J2rhdf1PGkhGJL7zd/e4sLAV1K4vaksUrBfFBEnQh2x3f0hmgJRT+IXsZl+Yul1aokdhx7oZhhOw1wTWQ12KiKgdIna2NrMzGXaERb4C+TgLpPeOkNuSKEG3tNfq+aw76FIeiBNp0H4XI3d7D7cg9juMN420sq1KHnfbjVnVX/ZjDQJM7M41wUnQIDAQAB
-----END PUBLIC KEY-----
'''

def _sign(data, signature):
    key = RSA.importKey(pubKey)
    h = SHA.new(data)
    verifier = PKCS1_v1_5.new(key)
    if verifier.verify(h, base64.b64decode(signature)):
        return True
    return False

def google_check_notify(request):
    p = request.POST.get('p')
    p = json.loads(p)
    resp = []
    for info in p:
        check_sum = info['signature']
        check_string = info['info']
        info = json.loads(info['info'])
        trade_no = info.get('orderId')
        purchase_token = info.get('purchaseToken')
        pay_id = int(info.get('developerPayload'))
        trade_status = info.get('purchaseState')
        price = PRODUCT_ID[info.get('productId').strip()]
        pay = get_pay(pay_id)
        currency = 'IDR'
        check_status = _sign(check_string, check_sum)
        if not check_status:
            continue
            raise ParamError('sign not pass, data: %s' % request.POST)

        user_id = pay.user_id
        if not pay or pay.status != PayStatus.SUBMIT.value:
            resp.append(pay_id)
            continue
            # raise ParamError('pay %s has been processed' % pay_id)

        total_fee = float(price) / _EXCHANGE_RATIO
        extend = {
            'title': u'deposit-googlewallet',
            'ext': {
                'trade_status': trade_status,
                'trade_no': trade_no,
                'total_fee': total_fee
            }
        }
        update_pay_ext(pay_id, extend['ext'])
        if int(trade_status) == 0:
            _LOGGER.info('Google Wallet Pay check order success, user_id:%s pay_id:%s, amount: %s, currency: %s' % (
                user_id, pay_id, total_fee, currency))
            set_gwallet_purchase_token(purchase_token, trade_no, user_id, pay_id)
            res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
            if res:
                _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                               'price': total_fee,
                               'channel': 'coda'})
                try:
                    pay_after_recharge(pay)
                    resp.append(pay_id)
                except Exception as e:
                    _LOGGER.exception(
                        'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
        else:
            add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
            _LOGGER.error(' Google Wallet response data show transaction failed, data: %s', request.POST)
    return resp


