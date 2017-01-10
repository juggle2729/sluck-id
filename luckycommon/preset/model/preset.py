# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


DEVICE_TYPE = Enum({
    "ANDROID": (1, "android"),
    "IOS": (2, "ios"),
    "WAP": (4, "mobile wap"),
    "WEB": (8, "pc web"),
    "INT_IOS_US": (16, "int ios us"),
    "INT_IOS_TW": (32, "int ios tw"),
    "INT_IOS_UK": (64, "int ios uk"),
})


class Preset(orm.Model):
    __tablename__ = "preset"
    id = orm.Column(orm.BigInteger, primary_key=True)
    device_type = orm.Column(orm.Integer)
    title = orm.Column(orm.TEXT)
    max_version = orm.Column(orm.Integer)
    min_version = orm.Column(orm.Integer)
    last_modified = orm.Column(orm.BigInteger)    # 同步版本号
    content = orm.Column(orm.TEXT)                # JSON
    remark = orm.Column(orm.TEXT)                 # 备注
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
