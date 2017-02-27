# -*- coding: utf-8 -*-
import requests
import logging
import hashlib
import json
from datetime import datetime

from django.conf import settings
from luckycommon.utils.exceptions import ParamError
from luckycommon.db import iap_receipt
from luckycommon.model.pay import PayType
from luckycommon.db.pay import create_pay, get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.api import parse_p


_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')



verifyReceiptURL = {
    'production': 'https://buy.itunes.apple.com/verifyReceipt',
    'sandbox': 'https://sandbox.itunes.apple.com/verifyReceipt'
}

APPLE_BID = 'com.as.treasure.snatch.tokoseribu.iShop'

PRODUCT_ID = {
    'TokoSeribu_15koins': 15.00,
    'TokoSeribu_29koins': 29.00,
    'TokoSeribu_45koins': 45.00,
    'TokoSeribu_99koins': 99.00,
    'TokoSeribu_199koins': 199.00
}


def _check_receipt(receipt, password='', env='production'):
    if env == 'production':
        request_url = verifyReceiptURL['production']
    else:
        request_url = verifyReceiptURL['sandbox']
    request_data = '{"receipt-data": "%s", "password": "%s"}' % (receipt, password)
    r = requests.post(request_url, request_data)
    if r.status_code == 200 :
        return r.json()
    else:
        return None


def check_sandbox_flag(request):
    tracks = parse_p(request.GET.get('p'))
    cvc = int(tracks.get('cvc', 0))
    svn = tracks.get('svn')
    if svn == 'iOS' and cvc == settings.IAP_VERSION_CODE and settings.IAP_FLAG:
        return True
    elif request.user_id in settings.IAP_TEST_ID:
        return True
    else:
        return False


def _get_hash_text(receipt):
    h = hashlib.sha1()
    h.update(receipt)
    return h.hexdigest()




def iap_check_notify(user_id, receipt_dic, env_flag):
    try:
        _LOGGER.info('IIIIIIIIIIIIIIIIIIIIIII request_info %s' % receipt_dic)
        receipt_data = receipt_dic.get('receipt')
        transaction_id = receipt_dic.get('transaction_id')
    except:
        raise ParamError('param invalid')
    #检查票据是否在无效票据表中
    receipt_date_hash = _get_hash_text(receipt_data)
    invalid_receipt_in_db = iap_receipt.get_invalid_receipt_by_hash_text(receipt_date_hash)
    if invalid_receipt_in_db: #通过hash值找到票据记录
        _LOGGER.error('IAP receipt invalid, user id: %s,receipt data: %s,receipt hash : %s' % (
            user_id, receipt_data, receipt_date_hash))
        return {'status': 1, 'msg': 'IAP receipt invalid'}
    #校验票据
    receipt_info = _check_receipt(receipt_data)
    if receipt_info == None:
        _LOGGER.error('IAP check receipt from AppStore error, user id: %s, transaction id: %s, '
                      'receipt_data: %s' % (user_id, transaction_id, receipt_data))
        return {'status': 2, 'msg': 'Check receipt error. Please retry'}
    receipt_status = receipt_info.get('status')
    if receipt_status not in [0, 21007]:
        _LOGGER.error('IAP receipt invalid, user id: %s, receipt data: %s, receipt hash : %s, return status %s' % (
            user_id, receipt_data, receipt_date_hash, receipt_status))
        # save invalid receipt to db
        iap_receipt.save_invalid_receipt(receipt_date_hash, receipt_data, receipt_status)
        return {'status': 1, 'msg': 'IAP receipt invalid'}
    if receipt_status == 21007:  #sandbox环境票据
        if env_flag:
            receipt_info = _check_receipt(receipt_data, env='sandbox')
            _LOGGER.info("IAP receipt check in sandbox environment")
            if receipt_info == None:
                _LOGGER.error('IAP check receipt from AppStore sandbox error, user id: %s, transaction id: %s, '
                              'receipt data: %s' % (user_id, transaction_id, receipt_data))
                return {'status': 2, 'msg': 'Check receipt error. Please retry'}
            receipt_status = receipt_info.get('status')
            if receipt_status != 0:
                _LOGGER.error("IAP receipt check in sandbox environment status error, user id: %s, transaction id: %s, "
                              "receipt data: %s, return status %s" % (
                    user_id, transaction_id, receipt_data, receipt_status))
                return {'status': 1, 'msg': 'IAP receipt invalid'}
        else:
            _LOGGER.error('IAP receipt environment is sandbox, user id: %s, receipt data: %s,'
                          ' receipt hash : %s, return status %s' % (
                user_id,receipt_data, receipt_date_hash, receipt_status))
            iap_receipt.save_invalid_receipt(receipt_date_hash, receipt_data, receipt_status)
            return {'status': 1, 'msg': 'IAP receipt invalid'}
    _LOGGER.info("IAP receipt App Store check Success, user id: %s, receipt info: %s" % (user_id, receipt_info))
    # 校验bundle id
    receipt = receipt_info.get('receipt')
    r_bid = receipt.get('bundle_id')
    if r_bid != APPLE_BID:
        _LOGGER.error("IAP receipt bid invalid,user id: %s, bid: %s" % (user_id, r_bid))
        # save invalid receipt to db
        iap_receipt.save_invalid_receipt(receipt_date_hash, receipt_data, 30000)
        return {'status': 1, 'msg': 'IAP receipt bid invalid'}

    in_app = receipt.get('in_app')
    purchase_info = in_app[0]
    r_product_id = purchase_info.get('product_id')
    r_transaction_id = purchase_info.get('transaction_id')
    # 检验 transaction_id 是否匹配
    if transaction_id != r_transaction_id:
        _LOGGER.error("IAP receipt bid invalid,user id: %s, transaction id: %s, "
                      "AppStore return transaction id: %s" % (user_id, transaction_id, r_transaction_id))
        return {'status': 1, 'msg': 'IAP receipt transaction not match'}
    # 检验 product_id 是否匹配
    if r_product_id not in PRODUCT_ID.keys():
        _LOGGER.error("IAP receipt product id invalid, user id: %s,purchase info: %s,product id: %s" % (
            user_id, purchase_info, r_product_id))
        iap_receipt.save_invalid_receipt(receipt_date_hash, receipt_data, 30001)
        return {'status': 1, 'msg': 'IAP receipt product id invalid'}
    # 发货数量
    pay_amount = PRODUCT_ID[r_product_id]
    extend = {
        'title': u'Apple-IAP',
        'ext': {
            'trade_status': 0,
            'trade_no': r_transaction_id,
            'total_fee': pay_amount
        }
    }
    receipt_in_db = iap_receipt.get_receipt_by_transaction_id(r_transaction_id)
    if receipt_in_db:
        if receipt_in_db.provide_status == 1:
            _LOGGER.info("IAP receipt has been delivery, user id: %s,transaction id: %s" % (user_id,r_transaction_id))
            return {'status': 1, 'msg': 'IAP receipt has been delivery'}
        else:
            # 补发
            _LOGGER.info("IAP receipt has in db and reprovide, user id: %s, transaction id: %s, pay id: %s" % (
                user_id, receipt_in_db.id, receipt_in_db.pay_id
            ))
            res = add_pay_success_transaction(user_id, receipt_in_db.pay_id, pay_amount, extend)
            if res:
                _LOGGER.info("IAP receipt reprovide success, user id: %s, transaction id: %s, "
                             "pay id: %s, pay mount: %s" % (
                    user_id, receipt_in_db.id, receipt_in_db.pay_id, pay_amount
                ))
                iap_receipt.update_receipt_provide_success(receipt_in_db.id)
                try:
                    pay = get_pay(receipt_in_db.pay_id)
                    pay_after_recharge(pay)
                except Exception as e:
                    _LOGGER.exception(
                        'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
                return {'status': 0, 'msg': 'ok'}
            else:
                _LOGGER.error("IAP receipt reprovide fail, user id: %s, transaction id: %s, "
                             "pay id: %s, pay mount: %s" % (
                                 user_id, receipt_in_db.id, receipt_in_db.pay_id, pay_amount
                             ))
                iap_receipt.update_receipt_provide_fail(receipt_in_db.id)
                return {'status': 2, 'msg': 'Delivery error, please retry.'}
    else:
        # 创建订单
        pay = create_pay(user_id, PayType.APPLE_IAP.value)
        pay.status = 1
        pay.save()
        _LOGGER.info("IAP receipt check success and provide, user id: %s, transaction id: %s, pay id: %s" %(
            user_id, r_transaction_id, pay.id
        ))
        update_pay_ext(pay.id, extend['ext'])
        iap_receipt.save_receipt(user_id, pay.id, receipt_data, receipt_info)
        res = add_pay_success_transaction(user_id, pay.id, pay_amount, extend)
        if res:
            _LOGGER.info("IAP receipt provide success, user id: %s, transaction id: %s, "
                         "pay id: %s, pay mount: %s" % (
                             user_id, r_transaction_id, pay.id, pay_amount
                         ))
            iap_receipt.update_receipt_provide_success(r_transaction_id)
            try:
                pay_after_recharge(pay)
            except Exception as e:
                _LOGGER.exception(
                    'pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
            return {'status': 0, 'msg': 'ok'}
        else:
            _LOGGER.info("IAP receipt provide fail, user id: %s, transaction id: %s, "
                         "pay id: %s, pay mount: %s" % (
                             user_id, r_transaction_id, pay.id, pay_amount
                         ))
            iap_receipt.update_receipt_provide_fail(r_transaction_id)
            return {'status': 2, 'msg': 'Delivery error, please retry.'}