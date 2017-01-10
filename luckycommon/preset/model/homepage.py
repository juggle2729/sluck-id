# coding=utf-8
from luckycommon.model import orm


class Homepage(orm.Model):
    __tablename__ = "homepage_lib"
    id = orm.Column(orm.BigInteger, primary_key=True)
    name = orm.Column(orm.TEXT)
    icon = orm.Column(orm.TEXT)
    # 0-没有tip, 1-打点, 2-左边文字, 3-右边文字, 4-背景色块
    type = orm.Column(orm.Integer)
    dot = orm.Column(orm.Integer)
    cmd = orm.Column(orm.TEXT)
    abtest = orm.Column(orm.Integer)
    remark = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
