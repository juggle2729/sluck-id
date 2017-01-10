# -*- coding: utf-8 -*-

import json
import urllib
import logging
import requests
from django.conf import settings
from django.utils.encoding import smart_unicode
from luckycommon.third.common.CryptoHelper import CryptoHelper
from luckycommon.utils.exceptions import DataError, ParamError
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.model.pay import PAY_TYPE, PAY_STATUS
from luckycommon.db.transaction import (add_pay_wait_transaction,
                                        add_pay_success_transaction,
                                        add_pay_fail_transaction)
from luckycommon.pay.handler import pay_after_recharge

WaresInfo = {
    "appvkey": "MIICXQIBAAKBgQCHsNy+ALpHQjR8ek4taTusBlIiVA+aO5V7hRvLu/+wE75BLQOCEQRtV2amS/7CccRXYxn212+zeJdpBYLlr7nhs2z7Q+AEBOigVBX0RYKXLMDfFRV8yTGNi6M40AgBFpFRzoG2z95AOLvtEqQn6Locjec4o3SUdavbnXVbfCACZQIDAQABAoGABTtll5HxnNPJsE8K+qdHHL/1pMs2+sx3XBbq1nU+S6zHNj4lF3vOfuTS2XCutxKp7nCszJ7L+NCajfsfa/nVofbodcjoaGmmHdJ+ACY10wqF33n3e6GLU3N44ub22jmiJd32W+Moi5KlmMW7MUxx1cO/bjIfUo1gTpnOLlheplUCQQC8RkTkZ0lAXOZSfsva7ON9/eSmN9/afgCJoFUsB1e50jjxjBl42A4mYbycgPc8NuoHrQIPXtTyEWBDms0C/DlHAkEAuIBMRLUTTakOvNJbWhMX1slCYGIPgbNZQtAY12O4NH2AYvbYcz6mc+SH2vC8nTOmqcQYoyCE/WMr0IFKcO888wJBAKUHHvnpgu60v3pOBBf4jotwUcxUq5XT3lrEPAPkx8NsfldTizw+fWCtSOsRrCSOqeJihqy8XgF0s6FufgcA2J8CQHnHLRAYmLIkyPZ2vhc5DP4W/znQ371THLKN2ieoyTfUMn6fwYRnsMRD7ivjxArawcHCDiT13PHGmG/aNsFOF2MCQQChowayfxu1FfnUo3n63YvWaDouhk0ajFPUo+MU3aJaFot6fsM/bWGyLXPdcHOHWO8JCV1Z+JCCu1CfhbKSJShy",
    "platpkey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDjl0g3yZ3FNdOuT58N5nhFk2sh4Zwp8/q5dYcAMS33vyHFa/YO0zmwa0sJGZTHfYP3oPHulD9k79Dm2l+rNPF1RVuAfyGtbVQ5O9ldYnK9Bz0uxQKUK/UtQqtuuU24QLVfrwzUYmovzfiCMYhxvNIsMNoDECyv8zgNE4ubQfqVSQIDAQAB",
}

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')


def iapppay_create_charge(pay, pay_amount, pay_type, return_url):

    # dirty condition
    # amount must >= 2, and not = 48
    if pay_amount < 2:
        pay_amount = 2
    if pay_amount == 48:
        pay_amount == 50
    # dir end

    crypto = CryptoHelper()
    privateKey = CryptoHelper.importKey(WaresInfo["appvkey"])
    cp = CPOrder()
    url = "http://ipay.iapppay.com:9999/payapi/order"
    body = {
        "appid": "3006298594",
        "cporderid": str(pay.id),
        "currency": "RMB",
        "appuserid": "unknow",
        "waresname": u"购买充值卡",
        "waresid": 1,
        "price": float(pay_amount),
        "cpprivateinfo": "unknow",
        "notifyurl": settings.IAPPPAY_TMP_NOTIFY_URL
    }
    result = cp.process_request(url, body)
    if pay_type == PAY_TYPE.IAPP_PAY_TMP:
        transid = json.loads(result['transdata']).get('transid')
        return {
            'transid': transid
        }
    elif pay_type == PAY_TYPE.IAPP_PAY_WAP:
        transid = json.loads(result['transdata']).get('transid')
        dict = {
            'transid': transid,
            'redirecturl': return_url
        }
        data = json.dumps(dict, ensure_ascii=False).encode('utf8')
        req_sign = crypto.sign(data, privateKey)
        return {
            'transdata': data,
            'sign': req_sign,
            'signtype': 'RSA'
        }


def check_notify_sign(request):

    crypto = CryptoHelper()
    platpkey = CryptoHelper.importKey(WaresInfo["platpkey"])
    try:
        request_body = smart_unicode(urllib.unquote(request.body).decode('utf8'))
    except Exception as e:
        request_body = str(urllib.unquote(request.body).decode('utf8'))
    result = crypto.segmentation_data(request_body, platpkey)
    if result:
        data = json.loads(result['transdata'])
        pay_id = data.get('cporderid')
        if not pay_id:
            _LOGGER.error("fatal error, out_trade_no not exists, data: %s" % data)
            raise ParamError('Pingpp event does not contain pay ID')

        pay = get_pay(pay_id)
        if not pay or pay.status != PAY_STATUS.SUBMIT:
            raise ParamError('pay %s has been processed' % pay_id)

        trade_status = int(data['result'])
        user_id = pay.user_id
        trade_no = data['transid']
        total_fee = data['money']

        extend = {
            'title': u'购卡充值',
            'ext': {
                'trade_status': trade_status,
                'trade_no': trade_no,
                'total_fee': total_fee
            }
        }

        update_pay_ext(pay_id, extend['ext'])

        if trade_status == 0:
            _LOGGER.info('iapppay check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
            res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'iapppay'})
            if res:
                try:
                    pay_after_recharge(pay)
                except Exception as e:
                    _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
        else:
            add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
            _LOGGER.error('iapppay response data show transaction failed, data: %s', data)
    else:
        raise DataError('iapppay notify process error: %s', request_body)


class CPOrder:
    def __init__(self):
        self.crypto = CryptoHelper()
        self.privateKey = CryptoHelper.importKey(WaresInfo["appvkey"])
        self.platpkey = CryptoHelper.importKey(WaresInfo["platpkey"])

    def process_request(self, url, body):
        req_text = json.dumps(body, ensure_ascii=False).encode('utf8')
        req_sign = self.crypto.sign(req_text, self.privateKey)
        http_request_body = {
            'transdata': req_text,
            'sign': req_sign,
            'signtype': 'RSA'
        }
        text = requests.post(url, data=http_request_body, timeout=1)
        s = text.content
        reqData = urllib.unquote(str(s)).decode('utf8')
        return self.crypto.segmentation_data(smart_unicode(reqData), self.platpkey)


if __name__ == '__main__':
    cp = CPOrder()
    url = "http://ipay.iapppay.com:9999/payapi/order"
    body = {
        "appid": "3003429238",
        "cporderid": "55df2xge1c0dc98c7398231cd",
        "currency": "RMB",
        "appuserid": "dddddd",
        "waresname": "购买游戏币",
        "waresid": 1,
        "price": 1.00,
        "cpprivateinfo": "fd",
        "notifyurl": "www.baidu.com"}
    cp.process_request(url, body)
