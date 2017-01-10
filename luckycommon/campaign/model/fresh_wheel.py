# -*- coding: utf-8 -*-
from luckycommon.model import orm


AWARD_RATIO = [{
    'start': 1, 'end': 40, 'coupon_tid': 289, 'desc': u'1元夺宝红包', 'index': 0,
},{
    'start': 40, 'end': 70, 'coupon_tid': 290, 'desc': u'2元夺宝红包', 'index': 2,
},{
    'start': 70, 'end': 90, 'coupon_tid': 291, 'desc': u'5元夺宝红包', 'index': 6,
},{
    'start': 90, 'end': 100, 'coupon_tid': 292, 'desc': u'10元夺宝红包', 'index': 8,
}]


class FreshWheel(orm.Model):
    """
    新手转盘
    """
    __tablename__ = "fresh_wheel"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.Integer)
    coupon_id = orm.Column(orm.Integer)
    award_desc = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
