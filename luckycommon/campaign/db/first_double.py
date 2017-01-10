# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime, timedelta

from luckycommon.campaign.model.first_double import *
from luckycommon.db.coupon import award_coupon_in_transaction
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.tz import local_now, to_local_ts

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_status(user_id):
    return FirstDouble.query.filter(FirstDouble.user_id == user_id).first()


@sql_wrapper
def apply(user_id):
    item = FirstDouble.query.filter(FirstDouble.user_id == user_id).first()
    if not item:
        item = FirstDouble()
        item.user_id = user_id
        item.apply_at = datetime.utcnow()
        item.save()
    return item


@sql_wrapper
def check_recharge(user_id, recharge_amount):
    item = FirstDouble.query.filter(FirstDouble.user_id == user_id).with_lockmode('update').first()
    if not item:
        item = FirstDouble()
        item.user_id = user_id
        item.apply_at = datetime.utcnow()
        item.save()
    if item.status == STATUS.AWARD:
        return
    for conf in AWARD_CONF:
        if recharge_amount >= conf['amount']:
            coupon_tid = conf['tid']
            local_today = local_now().replace(hour=0, minute=0, second=0)
            award_coupon_in_transaction(user_id, coupon_tid)
            for i in range(1, 10):
                start_date = local_today + timedelta(i)
                start_ts = to_local_ts(start_date)
                award_coupon_in_transaction(user_id, coupon_tid, start_ts=start_ts)
            item.recharge_price = recharge_amount
            item.coupons = json.dumps({"tid": coupon_tid, "count": 10})
            item.status = STATUS.AWARD
            orm.session.commit()
            return item
    return None
