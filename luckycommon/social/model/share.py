# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


SHARE_COUPON_INTERNAL_COUNT = 10
SHARE_COUPON_EXPIRE_TS = 3 * 24 * 3600
SHARE_TYPE = Enum({
    "APP": (1, u'分享app'),
    "DETAIL": (2, u'分享商品详情页'),
    "WIN": (3, u'分享中奖'),
})


class SocialShare(orm.Model):
    """
    每日分享
    """
    __tablename__ = "social_share"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    date = orm.Column(orm.VARCHAR)
    user_id = orm.Column(orm.Integer)
    share_type = orm.Column(orm.Integer)
    share_times = orm.Column(orm.Integer)
    extend = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
