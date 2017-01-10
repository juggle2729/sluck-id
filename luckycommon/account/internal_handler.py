# -*- coding: utf-8 -*-

import logging

from luckycommon.account.db import account as account_db
from luckycommon.utils.exceptions import DataError

_LOGGER = logging.getLogger('lucky')


def get_account(user_id, use_cache=False):
    return account_db.get_account(user_id, use_cache)


def get_online_info(user_id, token=None):
    return account_db.get_online_info(user_id, token)


def exists_account(register_type, register_num):
    return account_db.exists_account(register_type, register_num)


def get_third_account(third_id, third_account_type):
    return account_db.get_third_account(third_id, third_account_type)


def exists_nick_name(nick_name):
    return account_db.exists_nick_name(nick_name)


def bind_account(user_id, bind_attr, bind_value):
    bind_list = account_db.bind_account(user_id, bind_attr, bind_value)


def logout_user(user_id):
    return account_db.logout_user(user_id)


def login_account(login_type, login_num, password, extend=None):
    return account_db.login_account(login_type, login_num, password, extend)


def login_third_account(third_id, third_account_type, extend=None):
    return account_db.login_third_account(third_id, third_account_type, extend)


def logout_device(user_id, token):
    return account_db.logout_device(user_id, token)


def create_account(info, channel=None, package=None):
    account = account_db.create_account(info, channel, package)
    return account


def register_third_account(third_id, third_account_type, nickname, avatar_url, channel, package):
    account_dict = {
        'nick_name': nickname,
        'avatar_id': avatar_url
    }
    account = account_db.create_account(account_dict, channel, package)
    if not account:
        raise DataError('create account failed, account_dict: %s' % account_dict)
    third_account = account_db.create_third_account(account.id, third_id, third_account_type)
    if not third_account:
        raise DataError(
            'bind third account failed. account id: %s, third id: %s, third_account_type: %s' % (account.id, third_id, third_account_type))
    return account


def encode_password(passwd):
    return account_db.encode_password(passwd)
