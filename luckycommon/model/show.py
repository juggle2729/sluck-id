# -*- coding: utf-8 -*-
import time
from datetime import timedelta

from luckycommon.model import orm

from luckycommon.timer import TIMER_EVENT_TYPE, TimerEvent

from luckycommon.utils.tz import now_ts
from luckycommon.utils.types import Enum
from luckycommon.utils import id_generator
from luckycommon.utils.tz import local_now, local_to_utc

from django.template.loader import render_to_string


SHOW_STATUS = Enum({
    "WAIT_SHOW": (1L, "wait show"),
    "WAIT_VERIFY": (2L, "wait verify"),
    "VERIFY_SUCCESS": (4L, "verify success"),
    "VERIFY_FAIL": (8L, "verify fail"),
    "VERIFY_PRE": (16L, "pre verify"),   # 预审核
})


HIGHLIGHT_TAG = Enum({
    "digest": (1, "digest"),
})


class AnnounceShow(orm.Model):

    """
    晒单
    """
    __tablename__ = "announce_show"
    id = orm.Column(orm.BigInteger, primary_key=True)
    template_id = orm.Column(orm.Integer)
    term_number = orm.Column(orm.Integer)
    order_id = orm.Column(orm.Integer)
    user_id = orm.Column(orm.Integer)
    status = orm.Column(orm.Integer, default=1)
    title = orm.Column(orm.VARCHAR)
    content = orm.Column(orm.TEXT)                        # 正文
    images = orm.Column(orm.TEXT)                         # 图片列表，以逗号分隔
    verified_at = orm.Column(orm.Integer)                 # 审核时间戳
    verify_comment = orm.Column(orm.TEXT)                 # 审核评论
    verify_award = orm.Column(orm.Integer)                # 审核奖励积分数量
    highlight = orm.Column(orm.Integer, default=0)        # 高亮类型：精化帖
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)

    @classmethod
    def start_notify_timer(cls, show_id):
        notify_date = local_now().replace(hour=18, minute=0, second=0) + timedelta(2)
        execute_ts = int(time.mktime(local_to_utc(notify_date).timetuple()))
        event_msg = {'show_id': show_id}
        TimerEvent.submit(TIMER_EVENT_TYPE.SHOW_NOTIFY, event_msg, execute_ts)
