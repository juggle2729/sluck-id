# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


PRICE_UNIT = Enum({
    "RMB": (0L, "chinese RMB"),
    "USD": (1L, "US Dollar")
})

SOURCE_TYPE = Enum({
    "ZF": (2L, u"直付供应商"),
    "YJ": (5L, u"月结供货商"),
    "SELF": (3L, u"自主发货"),
    "OTHER": (4L, u"其他")
})

SHIPPING_TYPE = Enum({
    "NORMAL": (0L, u"普通商品"),
    "PHONE": (1L, u"手机号码"),
    "Q_COIN": (2L, u"Q币"),
    "BALANCE": (3L, u"夺宝币"),
    "EMAIL": (4L, u'Email')
})


class Goods(orm.Model):
    __tablename__ = "goods"
    id = orm.Column(orm.Integer, primary_key=True)
    name = orm.Column(orm.VARCHAR)
    price = orm.Column(orm.FLOAT)     # 商品单价
    unit = orm.Column(orm.Integer)    # 价格单位
    sold = orm.Column(orm.Integer)    # 已售出数量
    total = orm.Column(orm.Integer)   # 总库存数量
    num = orm.Column(orm.Integer, default=1)   # 对应货源的个数，用于自动发货
    source = orm.Column(orm.TEXT)     # 货源连接，以逗号分隔
    shipping_type = orm.Column(orm.Integer, default=0)
    source_type = orm.Column(orm.Integer)
    source_name = orm.Column(orm.VARCHAR)
    extend = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
