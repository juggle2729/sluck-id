# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


CHECK_TYPE = Enum({
    "DAILY_SIGN": (1L, "daily sign"),           # 每日签到
    "DAILY_SHARE": (2L, "daily share")          # 每日分享
})


DAILY_SIGN_AWARDS = [140, 170, 200]


DAILY_SHARE_AWARD = 0 # v3.2后分享不加积分


class AccountDailyCheck(orm.Model):
    """
    用户daily check log表
    """
    __tablename__ = "account_daily_check"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    date = orm.Column(orm.VARCHAR)                # 日期 '2015-12-30'
    check_type = orm.Column(orm.Integer)          # check类型
    check_times = orm.Column(orm.Integer)         # check次数
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class AccountSign(orm.Model):
    """
    用户签到表
    """
    __tablename__ = "account_sign"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    continuous_times = orm.Column(orm.Integer)    # 连续签到次数
    last_sign_at = orm.Column(orm.DATETIME)       # 上次签到时间
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
