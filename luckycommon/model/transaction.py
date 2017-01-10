# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


TRANSACTION_TYPE = Enum({
    "IN": (1L, "in"),                        # 充值
    "AWARD": (2L, "system award"),           # 系统奖励
    "BALANCE_BUY": (4L, "buy crowdfunding"), # 余额购买
    "TRANSFER_IN": (8L, "transfer in"),      # 转入
    "TRANSFER_OUT": (16L, "transfer out"),   # 转出
    "REFUND": (32L, "refund"),               # 退款
})


TRANSACTION_STATUS = Enum({
    "WAIT": (0L, "wait"),
    "DONE": (1L, "finished"),
    "FAIL": (2L, "fail")
})


class Transaction(orm.Model):
    __tablename__ = "transaction"
    id = orm.Column(orm.BigInteger, primary_key=True, autoincrement=False)
    user_id = orm.Column(orm.BigInteger)
    type = orm.Column(orm.Integer)
    # 关联的支付编号，refer Pay::id  type==1或2时，为None
    pay_id = orm.Column(orm.VARCHAR)
    status = orm.Column(orm.Integer)         # 交易是否完成，默认为0
    title = orm.Column(orm.VARCHAR)
    price = orm.Column(orm.FLOAT)            # 交易的金额
    balance = orm.Column(orm.FLOAT)          # 交易后的账户余额
    order_id = orm.Column(orm.BigInteger)    # 对应type==2，关联的订单编号，0表示不关联
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
    extend = orm.Column(orm.TEXT)            # JSON，关联购买信息
