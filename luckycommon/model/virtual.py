# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


class VirtualAwaitingPool(orm.Model):
    __tablename__ = "virtual_awaiting_pool"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    user_id = orm.Column(orm.Integer)
    nick_name = orm.Column(orm.VARCHAR)
    avatar_id = orm.Column(orm.VARCHAR)
    ip = orm.Column(orm.VARCHAR)
    phone = orm.Column(orm.VARCHAR)
    password = orm.Column(orm.VARCHAR)
    deleted = orm.Column(orm.Integer, default=0)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class VirtualPool(orm.Model):
    __tablename__ = "virtual_pool"
    user_id = orm.Column(orm.Integer, primary_key=True)
    token = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class AvatarPool(orm.Model):
    __tablename__ = "avatar_pool"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    avatar_id = orm.Column(orm.VARCHAR)
    used_times = orm.Column(orm.Integer)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
