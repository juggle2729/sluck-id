# -*- coding: utf-8 -*-
from luckycommon.account.model import orm


class SensorSwitch(orm.Model):
    __tablename__ = "sensor_switch"
    id = orm.Column(orm.BigInteger, primary_key=True)
    platform = orm.Column(orm.VARCHAR)
    build_number = orm.Column(orm.Integer)
    sensor_status = orm.Column(orm.Boolean)

