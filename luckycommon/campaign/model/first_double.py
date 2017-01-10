# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


STATUS = Enum({
    "APPLIED": (1L, "applied"),# 已报名
    "AWARD": (2L, "award"),    # 已发放奖励
})


LEAST_AMOUNT = 20
AWARD_CONF = [
    {'amount': 1000, 'tid': 205},
    {'amount': 500, 'tid': 206},
    {'amount': 200, 'tid': 207},
    {'amount': 50, 'tid': 208},
]


class FirstDouble(orm.Model):
    """
    首充翻倍活动 
    """
    __tablename__ = "first_double"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    recharge_price = orm.Column(orm.Integer) # 完成活动的充值金额
    status = orm.Column(orm.Integer, default=1)         # 状态 1 2
    coupons = orm.Column(orm.VARCHAR)
    apply_at = orm.Column(orm.DATETIME)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
