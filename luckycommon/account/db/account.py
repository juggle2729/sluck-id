# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from hashlib import md5

from django.conf import settings
from future.utils import raise_with_traceback
from sqlalchemy.exc import IntegrityError

from luckycommon.account.model import orm
from luckycommon.account.model.account import (AccountStatus, Account, AccountToken,
                                               AccountThird)
from luckycommon.cache import redis_cache
from luckycommon.utils import exceptions as err
from luckycommon.utils import id_generator
from luckycommon.utils.api import EnhencedEncoder
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.respcode import StatusCode

_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')
_BAN_VIRTUAL_LOGIN = settings.BAN_VIRTUAL_LOGIN


def encode_password(passwd):
    return md5(passwd).hexdigest()


@sql_wrapper
def get_account(user_id, use_cache=False):
    if use_cache:
        account_dict = redis_cache.get_account(user_id)
        if not account_dict:
            account = Account.query.filter(Account.id == user_id).first()
            if account:
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
def black_account(user_id, reason=''):
    account = get_account(user_id)
    json_extend = json.loads(account.extend or '{}')
    json_extend['black_reason'] = reason
    extend = json.dumps(json_extend, ensure_ascii=False)
    account.extend = extend
    account.status = 1
    account.save()
    _TRACKER.info({'user_id': user_id, 'type': 'black'})

@sql_wrapper
def get_logon_info(user_id):
    info = AccountToken.query.filter(AccountToken.user_id == user_id).order_by(
        AccountToken.created_at.desc()).first()
    if info:
        data = json.loads(info.extend or '{}')
        return data
    else:
        return {}


@sql_wrapper
def exists_nick_name(nick_name):
    account = Account.query.filter(Account.nick_name == nick_name).first()
    return account


@sql_wrapper
def get_account_by_phone(phone_num):
    account = Account.query.filter(Account.phone == phone_num).first()
    return account


@sql_wrapper
def exists_account(register_type, register_num):
    account = None
    if register_type == 'phone':
        account = Account.query.filter(Account.phone == register_num).first()
    else:
        account = Account.query.filter(Account.email == register_num).first()
    return account


@sql_wrapper
def get_third_account(third_id, third_account_type):
    third_account = AccountThird.query \
        .filter(AccountThird.third_account_type == third_account_type) \
        .filter(AccountThird.third_id == third_id) \
        .first()
    return third_account


@sql_wrapper
def get_third_account_by_uid(user_id):
    third_account = AccountThird.query .filter(AccountThird.account_id == user_id).first()
    return third_account


@sql_wrapper
def has_password(phone_num):
    account = Account.query.filter(Account.phone == phone_num).first()
    if account and account.password:
        return True
    else:
        return False


@sql_wrapper
def activate_account(user_id):
    account = Account.query.filter(Account.id == user_id).one()
    account.status = AccountStatus.NORMAL.value
    account.save()


@sql_wrapper
def bind_account(user_id, bind_attr, bind_value):
    bind_list = []
    account = Account.query.filter(Account.id == user_id).one()
    if not getattr(account, bind_attr):
        bind_list.append(bind_attr)
    setattr(account, bind_attr, bind_value)
    account.save()
    return bind_list


@sql_wrapper
def create_account(info, channel=None, package=None):
    account = Account()
    if 'password' in info:
        account.password = encode_password(info['password'])
    for k in 'country', 'phone', 'email', 'nick_name', 'avatar_id', 'is_virtual':
        if k in info:
            setattr(account, k, info[k])
    account.extend = json.dumps({'logon': False, 'chn': channel, 'pkg': package})
    try:
        account.save()
    except IntegrityError:
        raise_with_traceback(
            err.DataError(status=StatusCode.DUPLICATE_ACCOUNT))
    return account


@sql_wrapper
def create_third_account(account_id, third_id, third_account_type):
    third_account = AccountThird()
    third_account.account_id = account_id
    third_account.third_id = third_id
    third_account.third_account_type = third_account_type
    third_account.save()
    return third_account


@sql_wrapper
def delete_account(user_id):
    Account.query.filter(Account.id == user_id).update({'deleted': 1})
    orm.session.commit()


@sql_wrapper
def update_account(account_dict):
    if 'id' not in account_dict:
        raise err.ServerError('missing id when updating account, account_dict: %s' % account_dict)
    account = Account.query.filter(Account.id == account_dict.get('id')).one()
    if not account:
        raise err.DataError('account not exist: %s' % account_dict.get('id'))
    if 'password' in account_dict:
        account.password = encode_password(account_dict['password'])
    for k in ('phone', 'avatar_id', 'nick_name', 'desc'):
        if k in account_dict:
            setattr(account, k, account_dict[k])
    account.save()
    cache_value = json.dumps(
        account.as_dict(), cls=EnhencedEncoder, ensure_ascii=False)
    redis_cache.save_account(account.id, cache_value)
    return account


@sql_wrapper
def reset_passwd(user, password):
    user.password = encode_password(password)
    user.save()
    return user.id


@sql_wrapper
def login_account(login_type, login_num, password, extend=None):
    if login_type == 'phone':
        user = Account.query.with_for_update().filter(
            Account.phone == login_num).first()
    else:
        user = Account.query.with_for_update().filter(
            Account.email == login_num).first()
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
def login_third_account(third_id, third_account_type, extend=None):
    third_account = get_third_account(third_id, third_account_type)
    if not third_account:
        raise err.ThirdPartyError('third account not exist')
    account = Account.query.filter(Account.id == third_account.account_id).first()
    if not account:
        raise err.DataError('account bind with third account id: %s not exist' % third_account.id)
    if account.status == AccountStatus.BANNED.value:
        raise err.PermissionError('forbidden')
    if _BAN_VIRTUAL_LOGIN:
        if redis_cache.is_virtual_account(account.id):
            raise err.AuthenticateError(status=StatusCode.INVALID_USER)

    token_extend = None
    if redis_cache.is_virtual_account(account.id):
        account_token = AccountToken.query.filter(
            AccountToken.user_id == account.id).filter(
            AccountToken.deleted == 0).order_by(
            AccountToken.created_at.desc()).first()
        if account_token:
            token_extend = account_token.extend

    token = id_generator.generate_uuid()
    record = AccountToken()
    record.user_id = account.id
    record.token = token
    if token_extend:
        record.extend = token_extend
    else:
        record.extend = json.dumps(extend) if extend else '{}'
    record.deleted = 0
    record.save()
    account.token = token

    extend = json.loads(account.extend) if account.extend else {}
    logon = extend.get('logon')
    if not logon:
        extend['logon'] = True
        account.extend = json.dumps(extend)
        account.save()
    if logon is None:
        logon = True
    return account, logon


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
def search_user_by_phone(keyword):
    result = Account.query.filter(Account.phone.like("%%%s%%" % keyword)).all()
    return result


@sql_wrapper
def search_user_by_email(keyword):
    result = Account.query.filter(Account.email.like("%%%s%%" % keyword)).all()
    return result


@sql_wrapper
def get_user_by_uid(user_id):
    result = Account.query.filter(Account.id == user_id).all()
    if len(result) > 0:
        return result[0]
    else:
        return None


@sql_wrapper
def get_last_n_user(count):
    return Account.query.filter().order_by(Account.id.desc()).limit(count).all()
