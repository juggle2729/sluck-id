# -*- coding: utf-8 -*-
import json
import logging
from hashlib import md5
from decimal import Decimal
from datetime import datetime

from future.utils import raise_with_traceback
from sqlalchemy.exc import IntegrityError

from luckycommon.account.model.account import AccountStatus
from luckycommon.model import orm
from luckycommon.model.pay import Pay, PayStatus
from luckycommon.account.model.account import (Account, AccountToken, AccountThird)
from luckycommon.model.transaction import (Transaction, TRANSACTION_TYPE,
                                           TRANSACTION_STATUS)

from luckycommon.cache import redis_cache
from luckycommon.utils.api import EnhencedEncoder

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils import exceptions as err
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils import id_generator

from django.conf import settings

_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')
_BAN_VIRTUAL_LOGIN = settings.BAN_VIRTUAL_LOGIN


def encode_password(passwd):
    return md5(passwd.encode('utf-8')).hexdigest()


@sql_wrapper
def get_account(user_id, use_cache=False):
    if use_cache:
        account_dict = redis_cache.get_account(user_id)
        if not account_dict:
            account = Account.query.filter(Account.id == user_id).first()
            cache_value = json.dumps(account.as_dict(),
                                     cls=EnhencedEncoder, ensure_ascii=False)
            redis_cache.save_account(user_id, cache_value)
        else:
            account = Account()
            account.from_dict(json.loads(account_dict))
    else:
        account = Account.query.filter(Account.id == user_id).first()
    return account


@sql_wrapper
def get_account_in_ids(ids):
    if not ids:
        return []
    accounts = Account.query.filter(Account.id.in_(ids)).all()
    return accounts


@sql_wrapper
def get_logon_info(user_id):
    info = AccountToken.query.filter(AccountToken.user_id == user_id).order_by(
        AccountToken.created_at.desc()).first()
    if info:
        data = json.loads(info.extend or '{}')
        data.update({'token': info.token})
        return data
    else:
        return {}


@sql_wrapper
def exists_phone(phone_num):
    account = Account.query.filter(Account.phone == phone_num).first()
    return account


@sql_wrapper
def need_set_password(phone_num):
    account = Account.query.filter(Account.phone == phone_num).first()
    if account and not account.password:
        return True
    else:
        return False


@sql_wrapper
def create_account(info, chn=None):
    account = Account()
    account.phone = info['phone']
    account.password = encode_password(info['password'])

    for k in 'email', 'country', 'nick_name', 'avatar_id':
        setattr(account, k, info[k])
    if 'is_virtual' in info:
        account.is_virtual = info['is_virtual']
    account.extend = json.dumps({'logon': False, 'chn': chn})
    try:
        account.save()
    except IntegrityError:
        raise_with_traceback(
            err.DataError(status=StatusCode.DUPLICATE_ACCOUNT))
    return account


@sql_wrapper
def delete_account(user_id):
    Account.query.filter(Account.id == user_id).update({
        'deleted': 1,
        'updated_at': datetime.utcnow()
    })
    orm.session.commit()


@sql_wrapper
def black_account(user_id):
    """
    拉黑账户
    """
    Account.query.filter(Account.id == user_id).update({
        'status': 1,
        'updated_at': datetime.utcnow()
    })
    orm.session.commit()
    _TRACKER.info({'user_id': user_id, 'type': 'black'})


@sql_wrapper
def update_account(info):
    info.update({
        'updated_at': datetime.utcnow()
    })
    Account.query.filter(Account.id == info['id']).update(info)
    orm.session.commit()
    account = Account.query.filter(Account.id == info['id']).first()
    cache_value = json.dumps(
        account.as_dict(), cls=EnhencedEncoder, ensure_ascii=False)
    redis_cache.save_account(info['id'], cache_value)
    return account


@sql_wrapper
def reset_passwd(phone, password):
    user = Account.query.with_for_update().filter(
        Account.phone == phone).first()
    if not user:
        raise err.DataError(status=StatusCode.INVALID_USER)
    user.password = encode_password(password)
    user.save()
    return user.id


@sql_wrapper
def login_account(phone, password, device_type='', os_version='', extend=None):
    user = Account.query.with_for_update().filter(
        Account.phone == phone).first()
    if not user:
        raise_with_traceback(err.AuthenticateError(
            status=StatusCode.INVALID_USER))
    if user.status == AccountStatus.BANNED.value:
        raise err.PermissionError('forbidden')

    if _BAN_VIRTUAL_LOGIN:
        if redis_cache.is_virtual_account(user.id):
            raise_with_traceback(err.AuthenticateError(
                status=StatusCode.INVALID_USER))

    if encode_password(password) != user.password:
        raise_with_traceback(err.AuthenticateError(
            status=StatusCode.WRONG_PASSWORD))

    token_extend = None
    if redis_cache.is_virtual_account(user.id):
        account_token = AccountToken.query.filter(
            AccountToken.user_id == user.id).filter(
            AccountToken.deleted == 0).order_by(
            AccountToken.created_at.desc()).first()
        if account_token:
            token_extend = account_token.extend

    token = id_generator.generate_uuid()
    record = AccountToken()
    record.user_id = user.id
    record.token = token
    record.device_type = device_type
    record.os_version = os_version
    if token_extend:
        record.extend = token_extend
    else:
        record.extend = json.dumps(extend) if extend else '{}'
    record.deleted = 0
    record.save()
    user.token = token

    extend = json.loads(user.extend) if user.extend else {}
    logon = extend.get('logon')
    if not logon:
        extend['logon'] = True
        user.extend = json.dumps(extend)
        user.save()
    if logon is None:
        logon = True
    return user, logon


@sql_wrapper
def third_account_login(user_id, device_type='', os_version='', extend=None):
    user = Account.query.with_for_update().filter(
        Account.id == user_id).first()
    if not user:
        raise_with_traceback(err.AuthenticateError(
            status=StatusCode.INVALID_USER))

    token = id_generator.generate_uuid()
    record = AccountToken()
    record.user_id = user.id
    record.token = token
    record.device_type = device_type
    record.os_version = os_version
    record.extend = json.dumps(extend) if extend else '{}'
    record.deleted = 0
    record.save()
    user.token = token

    extend = json.loads(user.extend) if user.extend else {}
    logon = extend.get('logon')
    if not logon:
        extend['logon'] = True
        user.extend = json.dumps(extend)
        user.save()
    if logon is None:
        logon = True
    return user, logon


@sql_wrapper
def logout_device(user_id, token):
    AccountToken.query.filter(AccountToken.user_id == user_id).filter(
        AccountToken.token == token).update({
        'deleted': 1,
        'updated_at': datetime.utcnow()
    })
    orm.session.commit()


@sql_wrapper
def logout_user(user_id):
    AccountToken.query.filter(AccountToken.user_id == user_id).update({
        'deleted': 1,
        'updated_at': datetime.utcnow()
    })
    orm.session.commit()


@sql_wrapper
def get_online_info(user_id, token=None):
    if token:
        return AccountToken.query.filter(
            AccountToken.user_id == user_id).filter(
            AccountToken.token == token).first()
    else:
        return AccountToken.query.filter(
            AccountToken.user_id == user_id).filter(
            AccountToken.deleted == 0).order_by(
            AccountToken.created_at.desc()).first()


@sql_wrapper
def add_account_balance(user_id, pay_id, added_balance, extend):
    """
    充值
    """
    _LOGGER.info(
        'add account balance, user_id[%s] balance[%s]' % (
            user_id, added_balance))
    # update pay record status
    res = Pay.query.filter(Pay.id == pay_id).filter(
        Pay.status == PayStatus.SUBMIT.value).update({
        'status': PayStatus.DONE.value,
        'price': added_balance,
        'updated_at': datetime.utcnow()
    })
    if res:
        account = Account.query.filter(
            Account.id == user_id).with_lockmode('update').first()
        account.balance = account.balance + \
                          (0 if not added_balance else Decimal(added_balance))
        account.save(auto_commit=False)
        # add or modify transaction
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
        transaction.price = added_balance
        transaction.balance = account.balance
        transaction.status = TRANSACTION_STATUS.DONE
        transaction.save(auto_commit=False)
        orm.session.commit()
    else:
        _LOGGER.warn(
            'add account balance, cocurrency occured!, pay_id[%s]' % pay_id)
