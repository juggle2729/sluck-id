# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


ORDER_STATUS = Enum({
    "WAIT_PAY": (0L, u"已下单，待支付"),
    "PAYING": (1L, u"已支付，待确认"),
    "PAYED": (2L, u"已支付确认, 待开奖"),
    "LOSE": (3L, u"未中奖"),
    "AWARDED": (4L, u"已中奖，待领奖"),
    "WAIT_SHIP": (5L, u"已领奖，待发货"),
    "WAIT_RECEIPT": (6L, u"已发货，待收货"),
    "DEAL": (7L, u"已收货"),
    "PROCESSING": (11L, u"resell, processing"),
    "WAIT_AFFIRM": (12L, u"resell, wait for user affirm"),
    "AFFIRMED": (13L, u"user affirmed"),
    "SHOW": (8L, u"已晒单"),
})

SHIP_STATUS = Enum({
    "NORMAL": (0L, u"正常"),
    "CHARGING": (1L, u"自动充值中"),
    "CHARGE_FAILED": (2L, u"自动充值失败"),
    "SHIPPING": (3L, u"自动发货中"),
    "SHIPPING_FAILED": (4L, u"自动发货失败"),
    "ILLEGAL": (5L, u'非法订单')
})

RED_ENVELOPE_STATUS = Enum({
    'WAIT_EXCHANGE': (0L, u'待兑换'),
    'EXCHANGE_FAILED': (1L, u'兑换失败'),
    'EXCHANGED': (2L, u'兑换成功')
})


class Order(orm.Model):
    __tablename__ = "order"
    id = orm.Column(orm.BigInteger, primary_key=True, autoincrement=True)
    activity_id = orm.Column(orm.VARCHAR)
    goods_quantity = orm.Column(orm.Integer)  # 购买的数量
    total_price = orm.Column(orm.FLOAT)       # 订单总金额
    buyer = orm.Column(orm.BigInteger)        # 购买者的用户编号
    lucky_numbers = orm.Column(orm.TEXT)      # 夺宝号码list，以逗号分隔; 优化为只存数量
    status = orm.Column(orm.Integer)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
    # 订单支付时间字符串，精确到毫秒, 2015-11-09 22:30:05,134
    pay_at = orm.Column(orm.VARCHAR)
    receipt_address = orm.Column(orm.TEXT)    # 收货信息. json
    extend = orm.Column(orm.TEXT)             # 记录购买时的ip/GEO. json


class OrderNumber(orm.Model):
    """
    存储具体order的number
    """
    __tablename__ = "order_number"
    order_id = orm.Column(orm.BigInteger, primary_key=True)
    numbers = orm.Column(orm.TEXT)      # 夺宝号码list，以逗号分隔
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class AwardedOrder(orm.Model):
    """
    中奖订单
    """
    __tablename__ = "awarded_order"
    order_id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.BigInteger)    # 购买者的用户编号
    activity_id = orm.Column(orm.VARCHAR)
    activity_name = orm.Column(orm.Integer)
    term_number = orm.Column(orm.Integer)
    status = orm.Column(orm.Integer)        # >= AWARDED && <= SHOW
    ship_status = orm.Column(orm.Integer, default=0)
    receipt_address = orm.Column(orm.TEXT)    # 收货信息. json
    remark = orm.Column(orm.TEXT)           # 订单备注信息
    extend = orm.Column(orm.TEXT)
    shipping_coin = orm.Column(orm.SmallInteger, default=0)  # 是否以夺宝币方式发货
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class OrderRoute(orm.Model):
    """
    中奖订单的状态路径
    """
    __tablename__ = "order_route"
    id = orm.Column(orm.Integer, primary_key=True)
    order_id = orm.Column(orm.BigInteger)
    status = orm.Column(orm.Integer)        # >= AWARDED && <= SHOW
    content = orm.Column(orm.TEXT)          # 操作日志
    operator = orm.Column(orm.VARCHAR)      # 管理员姓名
    extend = orm.Column(orm.TEXT)           # 备注信息，比如管理审核评论, 物流信息
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class Area(orm.Model):
    __tablename__ = "area"
    id = orm.Column(orm.VARCHAR, primary_key=True)
    name = orm.Column(orm.VARCHAR)
    full_name = orm.Column(orm.VARCHAR)
    parent_id = orm.Column(orm.VARCHAR)
    zip_code = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class RedEnvelope(orm.Model):
    __tablename__ = "red_envelope"
    id = orm.Column(orm.VARCHAR, primary_key=True)
    order_id = orm.Column(orm.BigInteger)
    third_id = orm.Column(orm.VARCHAR)  # pingxx id
    open_id = orm.Column(orm.VARCHAR)  # weixin open_id
    status = orm.Column(orm.SmallInteger, default=0)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
    user_id = orm.Column(orm.BigInteger)
    price = orm.Column(orm.Integer)
