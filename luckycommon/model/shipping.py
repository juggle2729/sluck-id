# -*- coding:utf-8 -*-
from luckycommon.model import orm


class AutoShipping(orm.Model):
    """
    用于自动充值脚本
    """
    __tablename__ = "auto_shipping"
    order_id = orm.Column(orm.Integer, primary_key=True)
    shipping_type = orm.Column(orm.Integer, default=1)
    template_id = orm.Column(orm.Integer)
    user_id = orm.Column(orm.Integer)
    phone = orm.Column(orm.VARCHAR)         # 充值的号码
    price = orm.Column(orm.Integer)         # 充值金额
    status = orm.Column(orm.Integer, default=0)        # 0:正在处理  1:处理成功  2:处理失败
    response = orm.Column(orm.TEXT)         # 调用充值接口的返回数据
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
