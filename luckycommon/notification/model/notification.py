# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


NOTIFY_TYPE = Enum({
    "SYSTEM": (0L, u"系统公告"),
    "CAMPAIGN": (1L, u"活动相关消息"),
    "AWARD": (2L, u"中奖相关消息"),
})

NOTIFY_STATUS = Enum({
    "UNRELEASED": (0L, u"未发布"),
    "RELEASED": (1L, u"已发布")
})


class Notification(orm.Model):
    __tablename__ = "notification_user"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.BigInteger)
    sync_id = orm.Column(orm.BigInteger)    # 同步版本号, 在redis中生成
    notify_type = orm.Column(orm.Integer)   # 通知类型, 消息分类, 1 2
    content = orm.Column(orm.TEXT)          # 通知内容. JSON
    extend = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class SysNotification(orm.Model):
    """
    系统消息, 所有用户共享一个版本号
    """
    __tablename__ = "notification_sys"
    id = orm.Column(orm.BigInteger, primary_key=True)
    sync_id = orm.Column(orm.BigInteger)    # 同步版本号, 在redis中生成
    content = orm.Column(orm.TEXT)          # 通知内容. JSON
    status = orm.Column(orm.SmallInteger, default=0)   # 状态，已/未发布
    extend = orm.Column(orm.TEXT)           # 存放系统消息的filters
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
