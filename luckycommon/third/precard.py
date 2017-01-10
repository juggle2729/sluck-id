# -*- coding: utf-8 -*-
import hashlib
import json
import logging
from collections import OrderedDict

import requests
from django.conf import settings

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_fail_transaction
from luckycommon.db.transaction import add_pay_success_transaction
from luckycommon.model.pay import PayStatus, PayType
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import (ParamError, DataError, ServerError, AuthenticateError)

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_MERCHANT_ID = '47687'
_MERCHANT_ACCOUNT = 'luckysky.jsc@gmail.com'
_MERCHANT_PASSWD = 'd3d3807c1c50b1962e3e35eaf8eed510'
_MERCHANT_PASSWD_HASH = hashlib.md5('|'.join([_MERCHANT_ID, _MERCHANT_PASSWD])).hexdigest()

_PRECARD_URL = "https://www.nganluong.vn/mobile_card.api.post.v2.php"

_EXCHANGE_RATIO = settings.EXCHANGE_RATIO

_NGANLUONG_PRECARD_ERROR_DICT = {
    '99': 'Error, but undefined or without reason ',
    '01': 'Error, IP address to access API of NganLuong.vn is refused ',
    '02': 'Error, parameter sent from the merchant to NganLuong.vn is not correct ( wrong parameter name or missing parameter) ',
    '03': 'Error, merchant id does not exist or merchant is blocked connection to NganLuong.vn',
    '04': 'Error, checksum code is not correct (this error arises when communication code between merchant and NganLuong.vn is not correct or the order of params is not correct) ',
    '05': 'Account that used to receive money does not exist.',
    '06': 'Account that used to receive money is blocked or limited, impossible to accept transactions',
    '07': 'prepaid card has used already',
    '08': 'prepaid card is blocked',
    '09': 'out of date card',
    '10': 'unverified card',
    '11': 'Wrong format of prepaid card code',
    '12': 'Wrong serial number',
    '13': 'Wrong card code or serial number is not correct',
    '14': 'Prepaid card does not exist',
    '15': 'Prepaid card can not use',
    '16': 'Number of entering card code (enter wrong card code) is beyond the limits',
    '17': 'Telco system is error, card is not deducted',
    '18': 'Telco system is error or overloaded, maybe card is not deducted, should be work with NganLuong.vn to resolve.',
    '19': 'Connection from NganLuong.vn to Telco system is error, card is not deducted ( for ex: wrong connection para, this error is not related to merchant)',
    '20': 'Successful connection to Telco, card is deducted but not yet adding money on NganLuong.vn',
}


def generate_precard_gateway(pay):
    return settings.PRECARD_GATEWAY_URL % str(pay.id)


def pay_via_nganluong(pay, pin_card, card_serial, type_card):
    pay_id = pay.id
    user_id = pay.user_id
    payload = OrderedDict((
        ('func', 'cardcharge'),
        ('version', '2.0'),
        ('merchant_id', _MERCHANT_ID),
        ('merchant_account', _MERCHANT_ACCOUNT),
        ('merchant_password', _MERCHANT_PASSWD_HASH),
        ('pin_card', pin_card),
        ('card_serial', card_serial),
        ('type_card', type_card),
        ('ref_code', pay_id),
        ('client_fullname', 'test'),
        ('client_email', 'test@test.com'),
        ('client_mobile', '0986588099')
    ))

    _LOGGER.debug('ready to pay precard,%s %s %s %s %s' % (user_id, pay_id, pin_card, card_serial, type_card))
    r = requests.post(_PRECARD_URL, payload)
    if r.status_code == 200:
        _LOGGER.debug('nganluong precard response:%s' % r.text)
        ret_list = r.text.split('|')
        pay_status = str(ret_list[0])
        if pay_status == '00':
            # pay success
            try:
                total_fee = float(ret_list[10]) / _EXCHANGE_RATIO
                transaction_amount, transaction_id = ret_list[11], ret_list[12]
                extend = {
                    'title': u'charge-prepaid card',
                    'success': True,
                    'ext': {
                        'status_code': ret_list[0],
                        'pay_type': PayType.PRE_CARD_NG.value,
                        'pay_service': 'nganluong',
                        'transaction_amount': transaction_amount,
                        'transaction_id': transaction_id,
                        'card_info': {
                            'pin_card': pin_card,
                            'card_serial': card_serial,
                            'type_card': type_card
                        }
                    }
                }
                res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
                _LOGGER.info('Precard Pay check order success, user_id:%s pay_id:%s, amount: %s' % (user_id, pay_id, total_fee))
                if res:
                    _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                                   'price': total_fee,
                                   'channel': 'NganLuong'})
                    try:
                        pay_after_recharge(pay)
                    except Exception as e:
                        _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)' % (pay.id, e))
            except Exception as e:
                _LOGGER.error('precard pay success buy exception, pay_id:%s %s %s %s' % (pay_id, pin_card, card_serial, type_card))
            return True
        else:
            # pay fail
            total_fee = 0
            extend = {
                'title': u'recharge-precard',
                'success': False,
                'ext': {
                    'status_code': pay_status,
                    'pay_type': PayType.PRE_CARD_NG.value,
                    'pay_service': 'nganluong',
                    'card_info': {
                        'pin_card': pin_card,
                        'card_serial': card_serial,
                        'type_card': type_card
                    }
                }
            }
            _LOGGER.error('precard pay fail, pay_id:%s %s %s %s, reason :<%s> %s' % (
                pay_id, pin_card, card_serial, type_card, pay_status, _NGANLUONG_PRECARD_ERROR_DICT.get(pay_status)))
            add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
            return False
    else:
        _LOGGER.error('nganluong precard api not accessible')
        return False
