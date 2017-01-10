# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


AWARD_STATUS = Enum({
    "WAIT_SHIP": (1L, "wait ship"),      # 待发货
    "WAIT_RECEIPT": (2L, "shipping"),    # 已发货
    "DEAL": (4L, "shipping"),    # 已成交
})


DEFAULT_TIMES = 1 # 默认可参与一次
MAX_TIMES = 50  # 最大参与次数

TASK_CONF = [
    {'name': u'完成每日签到', 'status': 0, 'add_times': 1},
    {'name': u'参与1次夺宝', 'status': 0, 'add_times': 1},
    {'name': u'免费抢1次话费', 'status': 0, 'add_times': 1},
    {'name': u'进行1次充值', 'status': 0, 'add_times': 2},
    {'name': u'成功招募一个徒弟', 'status': 0, 'add_times': 3},
    {'name': u'成功中奖1次', 'status': 0, 'add_times': 2},
    {'name': u'发布1次晒单', 'status': 0, 'add_times': 2},
]


AWARD_RATIO = [{
    'start': 1, 'end': 45, 'name': u'30元宝',
},{
    'start': 45, 'end': 75, 'name': u'50元宝',
},{
    'start': 75, 'end': 90, 'name': u'1元红包',
},{
    'start': 90, 'end': 100, 'name': u'10元红包',
},{
    'start': 101, 'end': 102, 'name': u'50元话费',
},{
    'start': 200, 'end': 201, 'name': u'iPhone 6s 16g',
}]


class FortuneWheel(orm.Model):
    """
    每日转盘活动
    """
    __tablename__ = "fortune_wheel"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.Integer)
    date = orm.Column(orm.VARCHAR)
    apply_times = orm.Column(orm.Integer)     # 已参与次数
    left_times = orm.Column(orm.Integer)      # 剩余次数
    task_status = orm.Column(orm.VARCHAR)     # 当前的任务完成情况, JSON
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class FortuneWheelAward(orm.Model):
    """
    转盘活动中奖记录 
    """
    __tablename__ = "fortune_wheel_award"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.Integer)
    date = orm.Column(orm.VARCHAR)
    times_index = orm.Column(orm.Integer) # 第几次, 从1开始
    award_index = orm.Column(orm.Integer) # 奖品序号，从0开始
    status = orm.Column(orm.Integer)      # 中奖状态 1 2 4
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
