# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


class DailyAmount(orm.Model):
    __tablename__ = "strategy_daily_amount"
    id = orm.Column(orm.BigInteger, primary_key=True, autoincrement=True)
    date = orm.Column(orm.VARCHAR)           # 日期 '2015-12-30'
    amount_limit = orm.Column(orm.Integer)   # 限额
    current_amount = orm.Column(orm.Integer, default=0) # 当前额度
    current_count = orm.Column(orm.Integer, default=0)  # 当前次数
    manual_amount_limit = orm.Column(orm.Integer)   # 人工限额
    manual_amount = orm.Column(orm.Integer, default=0) # 当前进行的人工干预额度
    extend = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class StrategyConfig(orm.Model):
    __tablename__ = "strategy_config"
    id = orm.Column(orm.Integer, primary_key=True)
    amount_limit = orm.Column(orm.Integer)   # 默认限额
    manual_amount_limit = orm.Column(orm.Integer)   # 默认人工限额
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


PRIVILEGE_TYPE = Enum({
    "TYPE_A+": (0, "level A+"),  # (0,50]
    "TYPE_A": (1, "level A"),  # (0,50]
    "TYPE_B": (2, "level B"),  # (50,100]
    "TYPE_C": (3, "level C"),  # (100,500] 
    "TYPE_D": (4, "level D"),  # (500,1000]
    "TYPE_E": (5, "level E"),  # (1000,2000]
    "TYPE_F": (6, "level F"),  # (2000,4000]
    "TYPE_G": (7, "level G"),  # (4000,7000]
})


PRIVILEGE_CONF = [
    {'interval': [1, 2, 3, 4], 'net': -20.0},
    {'interval': [0.25, 0.5, 0.75, 1], 'net': -0.4},
    {'interval': [0.25, 0.5, 0.75, 1], 'net': -0.35},
    {'interval': [0.5, 1, 1.5, 2], 'net': -0.3},
    {'interval': [0.5, 1, 1.5, 2], 'net': -0.2},
    {'interval': [1, 2, 3, 4], 'net': -0.1},
    {'interval': [2, 4, 6, 8], 'net': 0},
    {'interval': [8, 12, 16, 20], 'net': 0.1},
    {'interval': [12, 24, 36, 48], 'net': 0.1},
]


# PRIVILEGE_INTERVALS = [50, 100, 500, 1000, 2000, 4000, 7000]
# for Indonesia
PRIVILEGE_INTERVALS = [100, 200, 1000, 2000, 4000, 8000, 14000]


class StrategyPrivilege(orm.Model):
    """
    策略特权
    """
    __tablename__ = "strategy_privilege"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    privilege_type = orm.Column(orm.Integer)        # 特权类型,A\B\C
    used = orm.Column(orm.Integer, default=0)       # 是否已使用
    activity_id = orm.Column(orm.VARCHAR)           # 使用的活动编号
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)

    @classmethod
    def calc_privilege_type(cls, target_amount):
        match_type = 1
        for amount in PRIVILEGE_INTERVALS:
            if target_amount <= amount:
               break
            match_type += 1
        return match_type

    @classmethod
    def range_price(cls, privilege_type):
        i_index = privilege_type
        if i_index < 0 or i_index >= len(PRIVILEGE_INTERVALS):
            return 0, 0
        if i_index == 0:
            min_amount = 0
            max_amount = PRIVILEGE_INTERVALS[i_index]
        else:
            min_amount = PRIVILEGE_INTERVALS[i_index-1]
            max_amount = PRIVILEGE_INTERVALS[i_index]
        return min_amount, max_amount


class StrategyAchievement(orm.Model):
    """
    经验成就 
    """
    __tablename__ = "strategy_achievement"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.Integer)                 # 用户编号
    level = orm.Column(orm.Integer)                   # 成就等级
    exp = orm.Column(orm.Integer)                     # 当前经验值
    privileges = orm.Column(orm.VARCHAR)              # 获得的特权编号，以逗号分隔
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
