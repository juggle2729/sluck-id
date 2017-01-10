# -*- coding: utf-8 -*-
from luckycommon.model import orm


AWARD_CREDIT = 1000


class FreshMission(orm.Model):
    """
    新手任务
    """
    __tablename__ = "new_fresh_mission"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    step_a = orm.Column(orm.Integer, default=0)          # 了解1元购
    step_b = orm.Column(orm.Integer, default=0)          # 成功购买1次
    step_c = orm.Column(orm.Integer, default=0)          # 成功充值1次
    step_d = orm.Column(orm.Integer, default=0)          # 获得好友返利充值
    status = orm.Column(orm.Integer, default=0)          # 是否激活，0：未激活， 1：已激活
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
