# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.model import orm
from luckycommon.campaign.model.fresh_wheel import *
from luckycommon.db.coupon import award_coupon_in_transaction

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils import exceptions as err


_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_wheel(user_id):
    return FreshWheel.query.filter(FreshWheel.user_id == user_id).with_lockmode('update').first()


@sql_wrapper
def play_wheel(user_id, coupon_tid, award_desc):
    item = FreshWheel.query.filter(FreshWheel.user_id == user_id
        ).with_lockmode('update').first()
    if not item:
        item = FreshWheel()
        item.user_id = user_id
        coupon = award_coupon_in_transaction(user_id, coupon_tid, coupon_from=u'新手转盘')
        item.coupon_id = coupon.id
        item.award_desc = award_desc
        item.save()
        return coupon
    else:
        raise err.ResourceInsufficient('reach limit', status=StatusCode.REACH_LIMIT)


@sql_wrapper
def get_award_timeline():
    return FreshWheel.query.order_by(FreshWheel.created_at.desc()).limit(10).all()
