# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum

CALLBACK_STATUS = Enum({
    "UNCALLED": (0L, u"未召回"),
    "PHONED": (1L, u"已电话"),
    "SMSED": (2L, u"已短信"),
    "COUPONED": (4L, u"已发红包"),
    "BACK": (8L, u"已召回")
})


class MissedVips(orm.Model):
    __tablename__ = "missed_vips"
    id = orm.Column(orm.BigInteger, primary_key=True)
    uid = orm.Column(orm.BigInteger)
    type = orm.Column(orm.SmallInteger, default=1)
    nick_name = orm.Column(orm.VARCHAR(32))
    phone = orm.Column(orm.VARCHAR(16))
    chn = orm.Column(orm.VARCHAR(32))
    active_days = orm.Column(orm.Integer)
    created_time = orm.Column(orm.DATETIME)
    updated_time = orm.Column(orm.DATETIME)
    lost_days = orm.Column(orm.Integer)
    recharge_amount = orm.Column(orm.Integer)
    rank = orm.Column(orm.Integer)
    pay_count = orm.Column(orm.Integer)
    win_count = orm.Column(orm.Integer)
    win_amount = orm.Column(orm.Integer)
    status = orm.Column(orm.SmallInteger, default=0)
    created_at = orm.Column(orm.VARCHAR(32))
    updated_at = orm.Column(orm.DATETIME)


class BackVips(orm.Model):
    __tablename__ = "back_vips"
    id = orm.Column(orm.BigInteger, primary_key=True)
    call_at = orm.Column(orm.VARCHAR(14))
    calc_at = orm.Column(orm.VARCHAR(14))
    lost_days = orm.Column(orm.Integer)
    total_count = orm.Column(orm.Integer)
    back_count = orm.Column(orm.Integer)
    recharge_count = orm.Column(orm.Integer)
    recharge_amount = orm.Column(orm.Integer)
    win_count = orm.Column(orm.Integer)
    win_amount = orm.Column(orm.Integer)
    coupon_amount = orm.Column(orm.Integer)
    pay_count = orm.Column(orm.Integer)
