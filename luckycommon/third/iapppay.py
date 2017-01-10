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
    "appvkey": "MIICXAIBAAKBgQCC7pa66ASqgZcL8DTqW2juXifdrzBa6eCct8OIztZV6nZEJxuRcBg5aszBoIG4KuhNRMBWUBg9WUE3ViXE5c5nRQtqOESSOJwwMGjrWaxTfrv/57wmdDJrQqP3DN+LKO7F1eoc69wDwP6Tr+++LS51mgmuaAPHwqXARjoa5H0TdwIDAQABAoGAfllVVXqO/ideJqQfvESH5vcvi2sCw8jL+xAOflfzWCeRB0WiAeBlUAszGmsUoy+sytvcq65RJeqa15anjfGiEn5fB0TM4cR5RMHKtmriW49HDFyfpYpf+EKi0SBCNRzXCGrCk0ZbLbD6risnbEqMni96x/mWkwyUkUX1Q1UojvkCQQC+QMwLnEvhPxO7MOmmGGVoBcRWSSw4tdnmzR1v2tCtx4MIGaR/xM59nZdxBHPjMaZ/hhB2Y4vjprWhyhU5A0PrAkEAsC3N88ait2pqZT98fMdQ6TtBay4x+9Tl5nmJByLlUc/RUH32XDBSJvtB6yVWyfpQAgQ5bfI5ockpLWpnCzynpQJBALezeVH8qIflj/e/Utu90qyOZPWr0bcwYCYrB7FpZvVlH3BC0kNMlNVVxVSrJ/rHhiy8Fkk59WjrH5YIulVCgeECQBcaSpGXEKtgpwcT5i0ureuHu7JkYmWVq3gno9JtvwiVaetWOUIpi/xUonZFdTYTPv6ksys5wlj22hF8jHqqv4kCQBfSaoyIe3dLYWLQB3RtaC6iNovArG62xM3kQ6BH5Ssxb3FLIIbsrW36QWpVw63XxkooIiZ6baz8/kNKidI0KgU=",
    "platpkey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCIAtDHCeaZjQFmlw4H/GNIrDAxVGCR2Y5VbtG5E7BmQH0bISSRBSRjPQOwcsO6zilcOL7BkkGVsPk0bxoHR8Ais8q604e6ti32T0KgXFHsxUmP/64diLiVv0hsTi6vvpfu04x1Ls3MHYYJPfT22n9kpnNUhKELNeRB5DR5na/8PQIDAQAB",
}

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')


def iapppay_create_charge(pay, pay_amount, pay_type, return_url):
    crypto = CryptoHelper()
    privateKey = CryptoHelper.importKey(WaresInfo["appvkey"])
    cp = CPOrder()
    url = "http://ipay.iapppay.com:9999/payapi/order"
    body = {
        "appid": "3003429238",
        "cporderid": str(pay.id),
        "currency": "RMB",
        "appuserid": "unknow",
        "waresname": u"购买充值卡",
        "waresid": 1,
        "price": float(pay_amount),
        "cpprivateinfo": "unknow",
        "notifyurl": settings.IAPPPAY_NOTIFY_URL
    }
    result = cp.process_request(url, body)
    if pay_type == PAY_TYPE.IAPP_PAY:
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
            'title': u'充值-爱贝',
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
