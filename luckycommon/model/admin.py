# -*- coding: utf-8 -*-
from django.conf import settings

from luckycommon.utils.types import Enum
from luckycommon.utils.orm import ArmoryOrm


orm = ArmoryOrm()
orm.init_conf(settings.ADMIN_CONF)

ROLE = Enum({
    "FORBIDDEN": (0, "forbidden"),
    "USER": (1, "user"),
    "SENIOR_USER": (2, "senior_user"),
    "MANAGER": (3, "manager"),
    "SENIOR_MANAGER": (4, "senior_manager"),
    "ADMIN": (5, "admin")
})

PERMISSION = Enum({
    "NONE": (0, "none"),
    "READ": (1, "read"),
    "WRITE": (2, "write"),
})


class User(orm.Model):
    __tablename__ = 'user'
    id = orm.Column(orm.BigInteger, primary_key=True)
    nickname = orm.Column(orm.VARCHAR)
    email = orm.Column(orm.VARCHAR)
    password = orm.Column(orm.VARCHAR)
    role = orm.Column(orm.SmallInteger)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class Permission(orm.Model):
    __tablename__ = 'permission'
    id = orm.Column(orm.BigInteger, primary_key=True)
    url = orm.Column(orm.VARCHAR)
    permission = orm.Column(orm.SmallInteger)
    min_role = orm.Column(orm.SmallInteger)
    desc = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class UserToken(orm.Model):
    __tablename__ = 'user_token'
    user_id = orm.Column(orm.BigInteger, primary_key=True)
    token = orm.Column(orm.VARCHAR, primary_key=True)
    deleted = orm.Column(orm.SmallInteger)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
