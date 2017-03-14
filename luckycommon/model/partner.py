# -*- coding: utf-8 -*-
from luckycommon.model import orm


class Partner(orm.Model):
    __tablename__ = "partner"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    user_id = orm.Column(orm.Integer)
    inviter_id = orm.Column(orm.Integer)  # 直接邀请者
    invite_list = orm.Column(orm.TEXT)  # 邀请者列表，逐级向上, 以逗号分隔
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class PartnerReward(orm.Model):
    """
    好友返利记录
    """
    __tablename__ = "partner_reward"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    user_id = orm.Column(orm.Integer)
    partner_id = orm.Column(orm.Integer)
    relation_level = orm.Column(orm.Integer)  # 关系级别，1级好友/2级好友
    amount = orm.Column(orm.Integer)  # 返利的积分额度
    balance = orm.Column(orm.Integer)  # 返利后的积分余额
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


DEFAULT_COUPON_STATUS = [
    {'count': 1, 'status': 0},
    {'count': 2, 'status': 0},
    {'count': 5, 'status': 0},
    {'count': 10, 'status': 0},
    {'count': 20, 'status': 0},
    {'count': 50, 'status': 0},
]

COUPON_LIST = [199, 200, 201, 202, 203, 204]


class PartnerCoupon(orm.Model):
    """
    收徒红包
    """
    __tablename__ = "partner_coupon"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    user_id = orm.Column(orm.Integer)
    partner_count = orm.Column(orm.Integer)  # 徒弟数量
    coupon_status = orm.Column(orm.TEXT)  # 红包状态
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
