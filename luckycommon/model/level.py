# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum

LEVEL_COUPON_STATUS = Enum({
    "NOT_AVAILABLE": (0L, "no coupon"),
    "CAN_ACTIVATE": (1L, "coupon can activate"),
    "ALREADY_ACTIVATED": (2L, "coupon already activated"),
    "CAN_NOT_ACTIVATE": (3L, "coupon can not activate"),
})


class Level(orm.Model):
    __tablename__ = "level"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.BigInteger)
    exp = orm.Column(orm.BigInteger)
    current_level = orm.Column(orm.Integer)
    coupon_status = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class WeekExp(orm.Model):
    __tablename__ = "week_exp"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.BigInteger)
    exp = orm.Column(orm.BigInteger)
    week_num = orm.Column(orm.BigInteger)
    year = orm.Column(orm.BigInteger)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
