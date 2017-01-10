# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum

from django.conf import settings


TEMPLATE_ID = settings.MISS_RETURN_TID
MAX_CONSUME_AMOUNT = 11
COUPON_TIDS = [209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219]


class MissReturn(orm.Model):
    """
    不中包赔活动 
    """
    __tablename__ = "miss_return"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    activity_id = orm.Column(orm.VARCHAR)
    consume_amount = orm.Column(orm.Integer)
    coupon = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
