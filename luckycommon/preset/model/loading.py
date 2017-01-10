# -*- coding: utf-8 -*-
from luckycommon.model import orm


class Loading(orm.Model):
    __tablename__ = "loading_lib"
    id = orm.Column(orm.BigInteger, primary_key=True)
    title = orm.Column(orm.TEXT)
    imageUrl = orm.Column(orm.TEXT)
    start_date = orm.Column(orm.VARCHAR)
    end_date = orm.Column(orm.VARCHAR)
    stay = orm.Column(orm.Integer)
    command = orm.Column(orm.TEXT)
    jump = orm.Column(orm.Boolean)
    abtest = orm.Column(orm.Integer)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
