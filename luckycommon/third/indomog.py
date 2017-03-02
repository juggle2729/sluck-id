# -*- coding: utf-8 -*-
import datetime
import hashlib
import logging

import requests

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

ORDER_URL = 'http://dev.indomog.com/indomog2/new_core/index.php/paywall/main'


def indomog_create_charge(pay, pay_amount, currency):
    # price = pay_amount / settings.SUPPORT_CURRENCIES[currency]['exchange_rate']
    price = pay_amount
    payload = {"RMID": '0910403545',
               "QID": pay['id'],
               "RC": 4200,
               "Alg": "ts",
               "AlgID": "hello244@mailinator.com",
               "Name": "Test Aja",
               "EmailHP": "hello244@mailinator.com",
               "IPD": "127.0.0.1",
               "Now": str(datetime.datetime.utcnow())[:19],
               "QUrlBackground": "http://testaja.qhios.com/a.jpg",
               "QUrlImage": "http://testaja.qhios.com/b.jpg",
               "QUrlLogo": "http://testaja.qhios.com/c.jpg",
               "QUrlSuccess": "http://id.lucky-gou.com/api/v1/pay/indomog/notify/%s/" % pay['id'],
               "QUrlPending": "http://testaja.qhios.com/pending",
               "QUrlCancel": "http://testaja.qhios.com/cancel",
               "PurchaseAmt": str(price),
               "PurchaseDesc": "payment for Toko Seribu",
               "BMod": "BCATRF, MANTRF, BPVTRF, BIITRF, BRITRF, BNITRF, BSMTRF, MOGACC, MOGVCH, KLKBCA, KPYBCA, SMSMAN, INTMAN, CC",
               }
    signature = hashlib.sha1(
        str(payload['RMID']) + str(payload['QID']) + str(payload['RC']) + str(payload['Alg']) + str(payload['AlgID']) + str(
            payload['Name']) + str(payload['EmailHP']) + str(payload['IPD']) + str(payload['Now']) + str(payload['QUrlBackground']) + str(
            payload['QUrlImage']) + str(payload['QUrlLogo']) + str(payload['QUrlSuccess']) + str(payload['QUrlPending']) + str(
            payload['QUrlCancel']) + str(payload['PurchaseAmt']) + str(payload['PurchaseDesc']) + str(
            payload['BMod']) + '123456').hexdigest()
    payload.update({'Signature': signature})

    _LOGGER.info("post data: %s" % payload)
    response = requests.post(ORDER_URL,
                             data=payload)
    print response.content


if __name__ == '__main__':
    pay = {'id': 77077}
    indomog_create_charge(pay, 66, None)
