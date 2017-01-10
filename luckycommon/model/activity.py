# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum
from luckycommon.utils import id_generator

from django.template.loader import render_to_string


TEMPLATE_STATUS = Enum({
    "START_READY": (0L, "ready to start"),
    "STARTED": (1L, "started"),
    "PAUSED": (2L, "paused")
})


ACTIVITY_STATUS = Enum({
    "START_READY": (0L, "ready to start"),
    "STARTED": (1L, "Started"),
    "ANNOUNCE_READY": (2L, "ready to annouced"),
    "ANNOUNCED": (4L, "Announced"),
    "EXPIRED": (8L, "Expired"),
    "PAUSED": (16L, "paused")    # 库存不足，暂停
})


class ActivityTemplate(orm.Model):
    __tablename__ = "activity_template"
    id = orm.Column(orm.Integer, primary_key=True)
    name = orm.Column(orm.VARCHAR)
    desc = orm.Column(orm.TEXT)
    short_title = orm.Column(orm.VARCHAR)
    cover = orm.Column(orm.VARCHAR)
    images = orm.Column(orm.TEXT)
    graphics = orm.Column(orm.TEXT)
    goods_id = orm.Column(orm.Integer)
    price = orm.Column(orm.FLOAT, default=1)            # 单次众筹价格(货币)
    unit = orm.Column(orm.Integer)
    buy_limit = orm.Column(orm.Integer)                 # 单人购买限制
    target_amount = orm.Column(orm.Integer)
    country = orm.Column(orm.VARCHAR)
    current_term = orm.Column(orm.Integer)
    status = orm.Column(orm.Integer, default=0)
    weight = orm.Column(orm.Integer, default=0)         # 权重，用于热门排序
    added_at = orm.Column(orm.DATETIME)                 # 上架时间
    pk = orm.Column(orm.Integer, default=0)             # PK场设定，0: 非pk场  2: 双人PK  3: 三人PK
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class Activity(orm.Model):
    __tablename__ = "activity"
    id = orm.Column(orm.VARCHAR, primary_key=True)
    template_id = orm.Column(orm.Integer)
    term_number = orm.Column(orm.Integer)
    name = orm.Column(orm.VARCHAR)
    desc = orm.Column(orm.TEXT)
    short_title = orm.Column(orm.VARCHAR)
    cover = orm.Column(orm.VARCHAR)
    images = orm.Column(orm.TEXT)              # 活动图片list，逗号分隔
    graphics = orm.Column(orm.TEXT)            # 图文详情list，逗号分隔
    goods_id = orm.Column(orm.Integer)
    # 单次众筹价格, 默认为1元，越南地区为2500元越南币
    price = orm.Column(orm.FLOAT, default=1)
    unit = orm.Column(orm.Integer)             # 最小购买次数，默认为1次, 10元专区的即为10
    buy_limit = orm.Column(orm.Integer)        # 单人购买限制
    pk = orm.Column(orm.Integer, default=0)             # PK场设定，0: 非pk场  2: 双人PK  3: 三人PK
    target_amount = orm.Column(orm.Integer)    # 目标次数
    current_amount = orm.Column(orm.Integer, default=0)   # 当前筹集次数
    status = orm.Column(orm.Integer)
    winner = orm.Column(orm.TEXT)              # 获奖幸运号码list, 逗号分隔
    extend = orm.Column(orm.TEXT)              # 开奖计算相关信息, JSON
    announced_at = orm.Column(orm.DATETIME)    # 开奖的时间
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)

    def resume(self, template):
        self.template_id = template.id
        self.term_number = template.current_term
        self.status = ACTIVITY_STATUS.STARTED

    @classmethod
    def next_from_template(cls, template, insufficient=False):
        instance = cls()
        instance.template_id = template.id
        instance.term_number = template.current_term if not insufficient else 0
        instance.id = id_generator.generate_uuid('activity:%s:%s' % (instance.template_id,
                                                                     instance.term_number))
        instance.name = template.name
        instance.short_title = template.short_title
        instance.desc = template.desc
        instance.cover = template.cover
        instance.images = template.images
        instance.graphics = template.graphics
        instance.goods_id = template.goods_id
        instance.price = template.price
        instance.unit = template.unit
        instance.buy_limit = template.buy_limit
        instance.pk = template.pk
        instance.target_amount = template.target_amount
        instance.current_amount = 0
        instance.status = ACTIVITY_STATUS.STARTED if not insufficient else ACTIVITY_STATUS.PAUSED
        return instance


class HotActivity(orm.Model):

    """
    热门活动，索引表
    """
    __tablename__ = "hot_activity"
    id = orm.Column(orm.BigInteger, primary_key=True)
    template_id = orm.Column(orm.Integer)
    term_number = orm.Column(orm.Integer)
    status = orm.Column(orm.Integer, default=1)
    unit = orm.Column(orm.Integer)
    target_amount = orm.Column(orm.Integer)               # 目标次数
    current_amount = orm.Column(orm.Integer, default=0)   # 当前筹集次数
    left_amount = orm.Column(orm.Integer)                 # 当前剩余次数
    # 热门指数，计算得到或来自于ActivityTemplate中的weight
    hot = orm.Column(orm.Integer)
    added_at = orm.Column(orm.DATETIME)                   # 上架时间，用于最新排序
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class UserActivity(orm.Model):

    """
    用户活动表，索引表
    """
    __tablename__ = "user_activity"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.BigInteger)
    activity_id = orm.Column(orm.VARCHAR)
    numbers = orm.Column(orm.TEXT)              # 号码list, 逗号分隔
    status = orm.Column(orm.Integer, default=1)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class ActivityWin(orm.Model):

    """
    活动中奖信息表
    """
    __tablename__ = "activity_win"
    activity_id = orm.Column(orm.VARCHAR, primary_key=True)
    lucky_number = orm.Column(orm.VARCHAR)              # 中奖号码
    winner = orm.Column(orm.BigInteger)                 # 获奖者编号
    order_id = orm.Column(orm.BigInteger)               # 获奖订单编号
    announce_info = orm.Column(orm.TEXT)                # 开奖信息，JSON
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class ActivityPK(orm.Model):

    """
    PK场活动配置表
    """
    __tablename__ = "activity_pk"
    activity_id = orm.Column(orm.VARCHAR, primary_key=True)
    target_amount = orm.Column(orm.Integer)
    pk = orm.Column(orm.Integer)                 # pk配置  2: 两人pk  3: 三人pk 
    pk_info = orm.Column(orm.VARCHAR)            # pk参与信息 {0: {'uid': '', 'count': 100}, 1: null, 2: null}
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
