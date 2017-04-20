# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from decimal import Decimal

from luckycommon.model import orm
from luckycommon.account.model.account import Account
from luckycommon.model.pay import PayStatus, Pay
from luckycommon.db.helper import list_object
from luckycommon.model.transaction import Transaction, TRANSACTION_STATUS, TRANSACTION_TYPE

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils import exceptions as err
from luckycommon.utils import id_generator
from luckycommon.db.helper import paginate

_LOGGER = logging.getLogger('lucky')

_FRESH_AWARD_PRICE = 1.0


@sql_wrapper
def list_transaction(query_dct):
    return list_object(query_dct, Transaction)


@sql_wrapper
def get_transactions(user_id, limit=0, offset=0, transaction_type=None):
    query = Transaction.query.filter(Transaction.user_id == user_id)
    count_query = orm.session.query(orm.func.count(Transaction.id)) \
        .filter(Transaction.user_id == user_id)

    if transaction_type is not None:
        junction = orm.or_
        type_filters = []
        if transaction_type & TRANSACTION_TYPE.IN:
            type_filters.append(Transaction.type == TRANSACTION_TYPE.IN)
        if transaction_type & TRANSACTION_TYPE.AWARD:
            type_filters.append(Transaction.type == TRANSACTION_TYPE.AWARD)
        if transaction_type & TRANSACTION_TYPE.BALANCE_BUY:
            type_filters.append(
                Transaction.type == TRANSACTION_TYPE.BALANCE_BUY)
        if transaction_type & TRANSACTION_TYPE.REFUND:
            type_filters.append(Transaction.type == TRANSACTION_TYPE.REFUND)

        query = query.filter(junction(*type_filters))
        count_query = count_query.filter(junction(*type_filters))

    count = count_query.all()[0][0]

    query = query.order_by(Transaction.created_at.desc())
    if limit > 0:
        query = query.limit(limit)
        query = query.offset(offset)
    return query.all(), count


@sql_wrapper
def add_pay_wait_transaction(user_id, pay_id, pay_amount, extend):
    """
    充值等待确认
    """
    # update pay record status
    res = Pay.query.filter(Pay.id == pay_id).filter(Pay.status == PayStatus.SUBMIT.value).update({
        'price': pay_amount,
        'updated_at': datetime.utcnow()
    })
    if res:
        transaction = Transaction.query.filter(
            Transaction.pay_id == pay_id).first()
        if not transaction:
            transaction = Transaction()
            transaction.id = id_generator.generate_long_id('transaction')
            transaction.pay_id = pay_id
            transaction.user_id = user_id
            transaction.type = TRANSACTION_TYPE.IN
        transaction.title = extend.get('title')
        transaction.extend = json.dumps(extend.get('ext'), ensure_ascii=False)
        transaction.price = 0 if not pay_amount else Decimal(pay_amount)
        transaction.balance = None
        transaction.status = TRANSACTION_STATUS.WAIT
        transaction.save(auto_commit=False)
        orm.session.commit()
        return True
    else:
        _LOGGER.warn(
            'add pay wait transaction, cocurrency occured!, pay_id[%s]' % pay_id)
    return False


@sql_wrapper
def add_pay_success_transaction(user_id, pay_id, pay_amount, extend):
    """
    充值成功
    """
    # update pay record status
    res = Pay.query.filter(Pay.id == pay_id).filter(Pay.status == PayStatus.SUBMIT.value).update({
        'status': PayStatus.DONE.value,
        'price': pay_amount,
        'updated_at': datetime.utcnow()
    })
    if not res:
        res = Pay.query.filter(Pay.id == pay_id).filter(Pay.status == PayStatus.FAIL.value).update({
            'status': PayStatus.DONE.value,
            'price': pay_amount,
            'updated_at': datetime.utcnow()
        })
    if res:
        account = Account.query.filter(
            Account.id == user_id).with_lockmode('update').first()
        account.balance = account.balance + \
            (0 if not pay_amount else Decimal(pay_amount))
        account.save(auto_commit=False)
        # add or modify transaction
        transaction = Transaction()
        transaction.id = id_generator.generate_long_id('transaction')
        transaction.pay_id = pay_id
        transaction.user_id = user_id
        transaction.type = TRANSACTION_TYPE.IN
        transaction.title = extend.get('title')
        transaction.extend = json.dumps(extend.get('ext'), ensure_ascii=False)
        transaction.price = pay_amount
        transaction.balance = account.balance
        transaction.status = TRANSACTION_STATUS.DONE
        transaction.save(auto_commit=False)
        orm.session.commit()
        return True
    else:
        _LOGGER.warn(
            'add pay success transaction, cocurrency occured!, pay_id[%s]' % pay_id)
    return False


@sql_wrapper
def add_pay_fail_transaction(user_id, pay_id, pay_amount, extend):
    """
    充值失败
    """
    # update pay record status
    res = Pay.query.filter(Pay.id == pay_id).filter(Pay.status == PayStatus.SUBMIT.value).update({
        'status': PayStatus.FAIL.value,
        'price': pay_amount,
        'updated_at': datetime.utcnow()
    })
    if res:
        transaction = Transaction()
        transaction.id = id_generator.generate_long_id('transaction')
        transaction.pay_id = pay_id
        transaction.user_id = user_id
        transaction.type = TRANSACTION_TYPE.IN
        transaction.title = extend.get('title')
        transaction.extend = json.dumps(extend.get('ext'), ensure_ascii=False)
        transaction.price = 0 if not pay_amount else Decimal(pay_amount)
        transaction.balance = None
        transaction.status = TRANSACTION_STATUS.FAIL
        transaction.save(auto_commit=False)
        orm.session.commit()
        return True
    else:
        _LOGGER.warn(
            'add pay fail transaction, cocurrency occured!, pay_id[%s]' % pay_id)
    return False


@sql_wrapper
def add_system_award_transaction(user_id, award_amount=_FRESH_AWARD_PRICE, title=u'系统奖励'):
    account = Account.query.filter(
        Account.id == user_id).with_lockmode('update').one()
    account.balance += Decimal(award_amount)
    transaction = Transaction()
    transaction.id = id_generator.generate_long_id('transaction')
    transaction.user_id = account.id
    transaction.type = TRANSACTION_TYPE.AWARD
    transaction.title = title
    transaction.price = award_amount
    transaction.balance = account.balance
    transaction.status = TRANSACTION_STATUS.DONE
    orm.session.add(transaction)
    orm.session.commit()
    _LOGGER.info('add system award, %s %s %s', user_id, award_amount, title)


@sql_wrapper
def get_consume(user_id):
    amount = orm.session.query(orm.func.sum(Transaction.price)). \
        filter(Transaction.user_id == user_id). \
        filter(Transaction.status == TRANSACTION_STATUS.DONE). \
        filter(Transaction.type == TRANSACTION_TYPE.BALANCE_BUY).first()[0]
    return amount


@sql_wrapper
def get_award(user_id):
    amount = orm.session.query(orm.func.sum(Transaction.price)). \
        filter(Transaction.user_id == user_id). \
        filter(Transaction.status == TRANSACTION_STATUS.DONE). \
        filter(Transaction.type == TRANSACTION_TYPE.AWARD).first()[0]
    return amount


@sql_wrapper
def get_pay_id_list(user_id, status=1):
    query = orm.session.query(Pay.id).filter(Pay.user_id==user_id, Pay.status==status).all()
    return map(lambda x: x[0], query)


@sql_wrapper
def get_transaction_info(user_id):
    query = orm.session.query(Transaction.type, Transaction.status, Transaction.extend)
    pay_id_list = get_pay_id_list(user_id, PayStatus.DONE)
    query_info = query.filter(Transaction.pay_id.in_(pay_id_list), \
                                Transaction.user_id==user_id).all()
    query_info = map(lambda x: dict(zip(("transaction_type", "transaction_status", "transaction_ex_info"), x)), \
			query_info)
    def _translate_info(key, dict_info):
        dict_info[key] = json.dumps(dict_info[key])
        return dict_info
    result_info_info = map(lambda x: _translate_info("transaction_ex_info", x), query_info)
    return (result_info_info)


@sql_wrapper
def transfer_coin(out_uid, in_uid, amount):
    """
    转账夺宝币
    """
    if out_uid == in_uid:
        raise err.ClientError("illegal")
    accounts = Account.query.filter(
        Account.id.in_([out_uid, in_uid])).with_lockmode('update').all()
    out_account = None
    in_account = None
    for account in accounts:
        if account.id == out_uid:
            out_account = account
        elif account.id == in_uid:
            in_account = account
    if not out_account or not in_account:
        raise err.ParamError("invalid account")
    if out_account.balance < amount:
        raise err.BalanceInsufficient("account balance insufficient")
    # 出账
    out_account.balance -= Decimal(amount)
    out_transaction = Transaction()
    out_transaction.id = id_generator.generate_long_id('transaction')
    out_transaction.user_id = out_account.id
    out_transaction.type = TRANSACTION_TYPE.TRANSFER_OUT
    out_transaction.title = str(in_uid)
    out_transaction.price = -amount
    out_transaction.balance = out_account.balance
    out_transaction.status = TRANSACTION_STATUS.DONE
    orm.session.add(out_transaction)
    # 入账
    in_account.balance += Decimal(amount)
    in_transaction = Transaction()
    in_transaction.id = id_generator.generate_long_id('transaction')
    in_transaction.user_id = in_account.id
    in_transaction.type = TRANSACTION_TYPE.TRANSFER_IN
    in_transaction.title = str(out_uid)
    in_transaction.price = amount
    in_transaction.balance = in_account.balance
    in_transaction.status = TRANSACTION_STATUS.DONE
    orm.session.add(in_transaction)
    orm.session.commit()


@sql_wrapper
def get_transfer_transactions(user_id, limit=0, offset=0):
    query = Transaction.query.filter(Transaction.user_id == user_id)
    query = query.filter(Transaction.type.in_([TRANSACTION_TYPE.TRANSFER_IN, TRANSACTION_TYPE.TRANSFER_OUT]))
    query = query.order_by(Transaction.created_at.desc())
    if limit > 0:
        query = query.limit(limit)
        query = query.offset(offset)
    return query.all()
