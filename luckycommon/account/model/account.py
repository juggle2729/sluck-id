# -*- coding: utf-8 -*-
from luckycommon.account.model import orm
from luckycommon.utils.custom_enum import CustomEnum


class AccountStatus(CustomEnum):
    NORMAL = 0
    BANNED = 1


class Account(orm.Model):
    __tablename__ = "account"
    id = orm.Column(orm.BigInteger, primary_key=True)
    phone = orm.Column(orm.VARCHAR)
    avatar_id = orm.Column(orm.VARCHAR)
    nick_name = orm.Column(orm.VARCHAR)
    password = orm.Column(orm.VARCHAR)
    email = orm.Column(orm.VARCHAR)
    country = orm.Column(orm.VARCHAR)
    desc = orm.Column(orm.VARCHAR)    # 个性签名
    balance = orm.Column(orm.FLOAT, default=0.0)     # 账户余额
    credit = orm.Column(orm.Integer, default=0)      # 账户积分
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
    extend = orm.Column(orm.TEXT)
    is_virtual = orm.Column(orm.Boolean, default=False)
    status = orm.Column(orm.Integer, default=0)


class AccountToken(orm.Model):
    __tablename__ = "account_token"
    user_id = orm.Column(orm.BigInteger, primary_key=True)
    token = orm.Column(orm.VARCHAR, primary_key=True)        # uuid
    device_type = orm.Column(orm.VARCHAR)
    os_version = orm.Column(orm.VARCHAR)
    deleted = orm.Column(orm.SMALLINT)
    extend = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class ThirdAccountType(CustomEnum):
    facebook = u'facebook'


class AccountThird(orm.Model):
    __tablename__ = "account_third"
    id = orm.Column(orm.BigInteger, primary_key=True, autoincrement=True)
    account_id = orm.Column(orm.BigInteger)
    third_account_type = orm.Column(orm.VARCHAR)       # 第三方登录类型
    third_id = orm.Column(orm.VARCHAR)       # 第三方登录id
    extend = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
