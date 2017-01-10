# -*- coding: utf-8 -*-
from luckycommon.model import orm


class Banner(orm.Model):
    __tablename__ = "banner_lib"
    id = orm.Column(orm.BigInteger, primary_key=True)
    title = orm.Column(orm.TEXT)
    image = orm.Column(orm.TEXT)
    start_ts = orm.Column(orm.BigInteger)
    end_ts = orm.Column(orm.BigInteger)
    cmd = orm.Column(orm.TEXT)
    abtest = orm.Column(orm.Integer)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
