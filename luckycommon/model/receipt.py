# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


class ReceiptAddress(orm.Model):
    """
    收货地址
    """
    __tablename__ = "receipt_address"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    user_id = orm.Column(orm.Integer)
    phone = orm.Column(orm.VARCHAR)
    name = orm.Column(orm.VARCHAR)
    address = orm.Column(orm.VARCHAR)
    addr_code = orm.Column(orm.TEXT)
    default = orm.Column(orm.Integer, default=0)
    deleted = orm.Column(orm.Integer, default=0)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


SHIPPING_TYPE = Enum({
    "EXPRESS": (0, u'快递'),
    "PHONE": (1, u'手机号'),
    "QQ": (2, u'QQ'),
    "COIN": (3, u'夺宝币'),
    "EMAIL": (4, u'邮箱'),
})


class ReceiptNumber(orm.Model):
    """
    虚拟物品收货号码
    """
    __tablename__ = "receipt_number"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    user_id = orm.Column(orm.Integer)
    shipping_type = orm.Column(orm.Integer)
    number = orm.Column(orm.VARCHAR)
    default = orm.Column(orm.Integer, default=0)
    deleted = orm.Column(orm.Integer, default=0)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
