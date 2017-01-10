# -*- coding: utf-8 -*-
from luckycommon.model import orm


class Discovery(orm.Model):
    __tablename__ = "discovery_lib"
    id = orm.Column(orm.BigInteger, primary_key=True)
    title = orm.Column(orm.TEXT)
    icon = orm.Column(orm.TEXT)
    start_ts = orm.Column(orm.BigInteger)
    end_ts = orm.Column(orm.BigInteger)
    desc = orm.Column(orm.TEXT)
    tag = orm.Column(orm.VARCHAR)
    cmd = orm.Column(orm.TEXT)
    abtest = orm.Column(orm.Integer)
    remark = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
