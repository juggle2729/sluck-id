# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


ACCOUNT_STATUS = Enum({
    "NORMAL": (0L, "normal account"),
    "BANNED": (1L, "banned account"),
    "WHITE": (2L, "white account"),
})


class Account(orm.Model):
    __tablename__ = "account"
    id = orm.Column(orm.BigInteger, primary_key=True)
    phone = orm.Column(orm.VARCHAR)
    avatar_id = orm.Column(orm.VARCHAR)
    nick_name = orm.Column(orm.VARCHAR)
    password = orm.Column(orm.VARCHAR)
    email = orm.Column(orm.VARCHAR)
    country = orm.Column(orm.VARCHAR)
    balance = orm.Column(orm.FLOAT, default=0.0)  # 账户余额
    credit = orm.Column(orm.Integer, default=0)   # 账户积分
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


THIRD_ACCOUNT_TYPE = Enum({
    "UXIN": (1L, "uxin"),           # 有信
    "WECHAT": (2L, "wechat"),
    "QQ": (3L, "qq")
})


class AccountThird(orm.Model):
    __tablename__ = "account_third"
    id = orm.Column(orm.BigInteger, primary_key=True, autoincrement=True)
    user_id = orm.Column(orm.BigInteger)
    login_type = orm.Column(orm.SMALLINT)       # 第三方登录类型
    login_id = orm.Column(orm.VARCHAR)       # 第三方登录id
    extend = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
