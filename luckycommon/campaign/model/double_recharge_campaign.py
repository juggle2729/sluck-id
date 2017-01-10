# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


class DoubleRechargeCampaign(orm.Model):
    """
    充值送翻倍红包活动
    """
    __tablename__ = "double_recharge_campaign"
    id = orm.Column(orm.BigInteger, primary_key=True)
    campaign_id = orm.Column(orm.Integer)     # 活动编号，如70010
    user_id = orm.Column(orm.Integer)         # 用户编号
    level = orm.Column(orm.Integer)           # 达成的等级, 1:50, 2:100...
    current_price = orm.Column(orm.Integer)   # 当前达成的金额
    coupons = orm.Column(orm.VARCHAR)         # 打开的红包编号，以逗号分隔
    is_double = orm.Column(orm.Integer, default=0)       # 是否双倍
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
