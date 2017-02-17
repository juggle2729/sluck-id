# -*- coding: utf-8 -*-
from luckycommon.model import orm






class IAPReceipt(orm.Model):
    __tablename__ = "iap_receipt"
    id = orm.Column(orm.VARCHAR, primary_key=True) #票据id
    user_id = orm.Column(orm.BigInteger)
    pay_id = orm.Column(orm.BigInteger)
    receipt = orm.Column(orm.TEXT)
    receipt_info = orm.Column(orm.TEXT)   # AppStore 返回的票据信息
    product_id = orm.Column(orm.VARCHAR)  # 物品id
    environment = orm.Column(orm.VARCHAR)
    provide_status = orm.Column(orm.Integer)  # 发货状态
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)

class IAPInvalidReceipt(orm.Model):
    __tablename__ = "iap_invalid_receipt"
    id = orm.Column(orm.VARCHAR, primary_key=True)  # 票据sha hash值
    receipt = orm.Column(orm.TEXT)
    status = orm.Column(orm.Integer, default=0)
    extend = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
