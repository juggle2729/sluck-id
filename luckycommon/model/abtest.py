# -*- coding: utf-8 -*-
from luckycommon.model import orm


class ABTest(orm.Model):
    __tablename__ = "abtest"
    id = orm.Column(orm.Integer, primary_key=True)
    name = orm.Column(orm.VARCHAR)
    content = orm.Column(orm.TEXT)  # json string
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
