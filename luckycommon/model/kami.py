# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum

class Kami(orm.Model):
    __tablename__ = "kami"
    id = orm.Column(orm.BigInteger, primary_key=True)
    order = orm.Column(orm.BigInteger)
    phone = orm.Column(orm.VARCHAR(20))
    sn = orm.Column(orm.VARCHAR(100))
    code = orm.Column(orm.VARCHAR(100))

