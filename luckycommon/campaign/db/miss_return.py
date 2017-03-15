# -*- coding: utf-8 -*-
import json
import logging
from datetime import timedelta

from luckycommon.model import orm
from luckycommon.campaign.model.miss_return import *
from luckycommon.db.coupon import award_coupon_in_transaction

from luckycommon.utils.orm import get_count
from luckycommon.utils.tz import local_now, to_local_ts
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils import exceptions as err


_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_status(user_id):
    return MissReturn.query.filter(MissReturn.user_id == user_id).first()


@sql_wrapper
def get_award_count():
    return get_count(MissReturn.query)


@sql_wrapper
def check_return(user_id, activity_id, consume_amount):
    item = MissReturn.query.filter(MissReturn.user_id == user_id)\
                           .with_lockmode('update').first()
    if item:
        return None
    item = MissReturn()
    item.user_id = user_id
    item.activity_id = activity_id
    item.consume_amount = consume_amount
    item.coupon = ''
    item.save()
    return item
