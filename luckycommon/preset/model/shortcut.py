# -*- coding: utf-8 -*-
from luckycommon.model import orm


class Shortcut(orm.Model):
    __tablename__ = "shortcut_lib"
    id = orm.Column(orm.BigInteger, primary_key=True)
    title = orm.Column(orm.TEXT)
    icon = orm.Column(orm.TEXT)
    command = orm.Column(orm.TEXT)
    abtest = orm.Column(orm.Integer)
    remark = orm.Column(orm.Integer)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
