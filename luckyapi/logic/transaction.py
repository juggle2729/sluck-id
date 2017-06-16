# -*- coding: utf-8 -*-
import logging

from future.utils import raise_with_traceback

from luckyapi.model.transaction import TransactionLite
from luckycommon.account.db.account import get_account
from luckycommon.db import pay as pay_db
from luckycommon.db import transaction as transaction_db
from luckycommon.db.activity import get_activity
from luckycommon.message import handler as message_handler
from luckycommon.message.model.message import *
from luckycommon.model.pay import PayType, PayStatus
from luckycommon.third import coda_pay, fortumo_pay, nganluong, paypal_pay, precard, doku, mimo_pay, bluepay
from luckycommon.utils.exceptions import AuthenticateError, ParamError
from luckycommon.utils.template import generate_from_template
from luckycommon.utils.tz import utc_to_local

_LOGGER = logging.getLogger('lucky')

_DEFAULT_PAGE_SIZE = 20


def get_user_transactions(user_id, page, size, transaction_type):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit

    transaction_list = []
    transactions, count = transaction_db.get_transactions(
        user_id, limit, offset, transaction_type)
    for transaction in transactions:
        tran = TransactionLite()
        tran.status = transaction.status
        tran.title = transaction.title
        tran.price = transaction.price
        tran.balance = transaction.balance
        tran.time = utc_to_local(
            transaction.created_at).strftime('%Y-%m-%d %H:%M:%S')
        transaction_list.append(tran)

    return transaction_list, count


def create_pay_id(user_id, pay_type):
    if pay_type not in PayType.values():
        raise ParamError('Pay type not support')

    pay = pay_db.create_pay(user_id, pay_type)
    return pay.id


def view_pay_status(pay_id):
    pay = pay_db.get_pay(pay_id)
    if not pay:
        raise AuthenticateError('pay id invalid')
    return pay


def submit_pay(user_id, pay_id, pay_amount, pay_context, return_url):
    pay = pay_db.submit_pay_commit(pay_id, user_id)
    if not pay:
        raise AuthenticateError('pay id invalid')
    if pay.status != PayStatus.SUBMIT.value:
        raise AuthenticateError('pay status invalid')

    try:
        activity_id = pay_context['activity_id']
        quantity = pay_context['quantity']
        if activity_id != 0:
            activity = get_activity(activity_id, need_fill=False)
            if not activity or quantity <= 0:
                raise ParamError('activity id invalid')
            pay_db.fill_pay(pay_id, pay_amount, activity_id, quantity)

        update_extend = {}
        if pay_context.get('buy_list'):
            pay_db.fill_pay(pay_id, pay_amount, activity_id, quantity)
            update_extend.update({'buy_list': pay_context['buy_list']})
        if pay_context.get('coupon'):
            update_extend.update({'coupon': pay_context['coupon']})
        if pay_context.get('pk_size'):
            update_extend.update({'pk_size': pay_context['pk_size']})
        if update_extend:
            pay_db.update_pay_ext(pay_id, update_extend)

        # do real pay
        pay_type = pay.pay_type
        if pay_type == PayType.NGANLUONG.value:
            _LOGGER.info('start pay by Nganluong, pay_id[%s]' % pay_id)
            pay_url = nganluong.ewallet_send_order(pay, pay_amount)
            return {'charge': pay_url, 'type': 'url'}
        if pay_type == PayType.PAYPAL_EC.value:
            charge = paypal_pay.paypal_create_charge(pay, pay_amount)
            _LOGGER.info(
                'start pay by Paypal express checkout, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.CODA_PAY.value:
            charge = coda_pay.coda_create_charge(pay, pay_amount, 'IDR')
            _LOGGER.info('start pay by Coda Pay, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.FORTUMO_PAY.value:
            charge = fortumo_pay.fortumo_create_charge(pay, return_url)
            _LOGGER.info('start pay by Fortumo Pay, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.PRE_CARD_NG.value:
            charge = precard.generate_precard_gateway(pay)
            _LOGGER.info('start pay by Nganluong precard, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.PAYSSION.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.EWALLET.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.BLUEPAY_SDK_SMS.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.BLUEPAY_SDK_MOGPLAY.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.BLUEPAY_SDK_GAME_ON.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.ONLINE_BANK.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.MANDIRI_ECASH.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.CARRIER_BILLING.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.TELCO_VOUCHER.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.MIMO_BCA.value:
            charge = mimo_pay.mimo_create_charge(pay, pay_amount, 'IDR')
            _LOGGER.info('start pay by mimo bca, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.MIMO_TELKOMSEL.value:
            charge = mimo_pay.mimo_create_charge(pay, pay_amount, 'IDR', pay_method='telkomsel')
            _LOGGER.info('start pay by mimo telkomsel, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.MIMO_INDOSAT.value:
            charge = mimo_pay.mimo_create_charge(pay, pay_amount, 'IDR', pay_method='indosat')
            _LOGGER.info('start pay by mimo indosat, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.MIMO_THREE.value:
            charge = mimo_pay.mimo_create_charge(pay, pay_amount, 'IDR', pay_method='three')
            _LOGGER.info('start pay by mimo three, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.MIMO_XL.value:
            charge = mimo_pay.mimo_create_charge(pay, pay_amount, 'IDR', pay_method='xl')
            _LOGGER.info('start pay by mimo xl, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.CODA_SMS.value:
            _LOGGER.info('start pay by coda sms, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.BLUEPAY_SDK_CONVENNIENCE_STORE.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.BLUEPAY_SDK_ATM.value:
            _LOGGER.info('start pay by payssion, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.GOOGLE_BILLING.value:
            _LOGGER.info('start pay by google billing, pay_id[%s]' % pay_id)
            return {}
        if pay_type == PayType.DOKU_WALLET.value:
            charge = doku.doku_create_charge(pay, pay_amount, 'wallet')
            _LOGGER.info('start pay by doku, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'html_text'}
        if pay_type == PayType.DOKU_VISA.value:
            charge = doku.doku_create_charge(pay, pay_amount, 'visa')
            _LOGGER.info('start pay by doku, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'html_text'}
        if pay_type == PayType.BLUEPAY_SMS.value:
            charge = bluepay.bluepay_create_charge(pay, pay_amount, 'sms')
            _LOGGER.info('start pay by bluepay, pay_id[%s]' % pay_id)
            return {'charge': charge, 'type': 'url'}
        if pay_type == PayType.SELF_RECHARGE_CARD.value:
            _LOGGER.info('start pay by self recharge card, pay_id[%s]' % pay_id)
            return {'charge': '', 'type': 'native'}
        raise ParamError('pay type not support!')
    except Exception as e:
        pay_db.submit_pay_revert(pay_id)
        raise_with_traceback(e)


def transfer_to_other(user_id, other_id, amount):
    """
    转账给他人
    """
    transaction_db.transfer_coin(user_id, other_id, amount)
    data_dict = {
        'amount': amount,
    }
    content = generate_from_template(
        'transfer_msg', data_dict=data_dict, has_title=False)
    success, msg = message_handler.send_message(
        user_id, other_id, content, msg_type=MESSAGE_TYPE.TRANSFER)
    _LOGGER.info('%s transfer %s coins to %s', user_id, amount, other_id)


def get_transfer_records(user_id, page, size):
    """
    查看转账记录
    """
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    transaction_list = []
    transactions = transaction_db.get_transfer_transactions(
        user_id, limit, offset)
    for transaction in transactions:
        other_id = int(transaction.title)
        other_account = get_account(other_id)
        transfer_price = transaction.price
        transfer_time = utc_to_local(
            transaction.created_at).strftime('%Y-%m-%d %H:%M:%S')
        transaction_list.append({
            'other_id': other_id,
            'other_avatar': other_account.avatar_id,
            'other_name': other_account.nick_name,
            'price': transfer_price,
            'time': transfer_time,
        })

    return transaction_list
