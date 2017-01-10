# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


class BoxRechargeCampaign(orm.Model):
    """
    宝箱充值活动 
    """
    __tablename__ = "box_recharge_campaign"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    campaign_id = orm.Column(orm.VARCHAR)
    balance = orm.Column(orm.Integer)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class BoxRecord(orm.Model):
    """
    开宝箱记录
    """
    __tablename__ = "box_record"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    campaign_id = orm.Column(orm.VARCHAR)
    consume_price = orm.Column(orm.Integer)
    balance = orm.Column(orm.Integer)
    coupons = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
