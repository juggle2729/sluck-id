# -*- coding: utf-8 -*-
from luckycommon.model import orm


class Lottery(orm.Model):
    __tablename__ = "lottery"
    id = orm.Column(orm.Integer, primary_key=True)
    phase = orm.Column(orm.VARCHAR)
    number = orm.Column(orm.VARCHAR)
    reference = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
