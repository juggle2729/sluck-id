# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


SUNDAY_TIDS = [500, 501, 502, 503, 504, 505, 506]


STATUS = Enum({
    "NOTSTART": (0L, "not start"),
    "ONGOING": (1L, "ongoing"),
    "DONE": (2L, "done"),
})


TIME_CONF = [{
        'start_time': '10:30:00',
        'end_time': '23:59:59',
        'template_id': 500,
        'stock': 2
    },{
        'start_time': '12:30:00',
        'end_time': '23:59:59',
        'template_id': 501,
        'stock': 2
    },{
        'start_time': '14:30:00',
        'end_time': '23:59:59',
        'template_id': 502,
        'stock': 2
    },{
        'start_time': '16:30:00',
        'end_time': '23:59:59',
        'template_id': 503,
        'stock': 2
    },{
        'start_time': '18:30:00',
        'end_time': '23:59:59',
        'template_id': 504,
        'stock': 2
    },{
        'start_time': '20:30:00',
        'end_time': '23:59:59',
        'template_id': 505,
        'stock': 2
    },{
        'start_time': '22:30:00',
        'end_time': '23:59:59',
        'template_id': 506,
        'stock': 2
    }
]


class SundayApply(orm.Model):
    """
    活动报名
    """
    __tablename__ = "sunday_apply"
    id = orm.Column(orm.Integer, primary_key=True)
    term_id = orm.Column(orm.VARCHAR)                   # 期号，取活动开启当天的日期，如'20160522'
    user_id = orm.Column(orm.Integer)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class SundayRecord(orm.Model):
    __tablename__ = "sunday_record"
    id = orm.Column(orm.Integer, primary_key=True)
    activity_id = orm.Column(orm.VARCHAR)
    user_id = orm.Column(orm.Integer)
    return_amount = orm.Column(orm.Integer)          # 总返还金额
    first_amount = orm.Column(orm.Integer)           # 第一次返还金额
    second_amount = orm.Column(orm.Integer)          # 第二次返还金额
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
