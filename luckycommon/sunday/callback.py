# -*- coding: utf-8 -*-
import json
import time
import logging
from datetime import timedelta

from luckycommon.cache import redis_cache
from luckyapi.logic import coupon as coupon_handler

from luckycommon.sunday.db import sunday as sunday_db

from luckycommon.db import activity as activity_db
from luckycommon.order.db import order as order_db
from luckycommon.db import coupon as coupon_db

from luckycommon.timer import TIMER_EVENT_TYPE, TimerEvent

from luckycommon.utils.tz import local_now, local_to_utc


_LOGGER = logging.getLogger('worker')


COUPON_RANGE = xrange(1000, 1250) # 250个直减红包id列表，按额度从小到大排序


def _current_term():
    return redis_cache.get_current_sunday_term()


def first_return_back(activity_id):
    """
    第一次返还50%
    """
    _LOGGER.info('start first return back, %s', activity_id)
    term_id = _current_term()
    if not term_id:
        _LOGGER.warn('current term id is None')
        return
    apply_items = sunday_db.get_applys_by_term(term_id)
    apply_uids = [item.user_id for item in apply_items]
    user_activitys = activity_db.get_activity_users(activity_id)
    for user_activity in user_activitys:
        try:
            user_id = user_activity.user_id
            if user_id not in apply_uids:
                _LOGGER.warn('user %s not apply sunday term %s', user_id, term_id)
                continue
            nums = user_activity.numbers.split(',')
            buy_amount = len(nums)
            if buy_amount < 10:
                continue
            # check coupon mount
            orders, count = order_db.get_activity_orders(activity_id, user_id)
            coupon_list = []
            for order in orders:
                try:
                    extend = {} if not order.extend else json.loads(order.extend) or {}
                    if 'coupon' in extend:
                        coupon_list.append(int(extend['coupon']))
                except:
                    pass
            coupon_amount = 0
            for coupon_id in coupon_list:
                coupon = coupon_db.get_coupon_by_id(coupon_id)
                coupon_amount += coupon.price

            consume_amount = buy_amount - coupon_amount
            if buy_amount <= 50:
                consume_amount = consume_amount / 2
            first_return_amount = consume_amount/2 + consume_amount%2
            sunday_db.create_first_record(user_id, activity_id, consume_amount, first_return_amount)
            # send coupon
            coupon_index = first_return_amount - 1
            if coupon_index >= len(COUPON_RANGE):
                _LOGGER.error('sunday campaign, coupon index %s out of range', coupon_index)
                continue
            coupon_id = COUPON_RANGE[coupon_index]
            coupon_extend = {"add_by": "sunday_campaign", "activity_id": activity_id}
            coupon_extend = json.dumps(coupon_extend, ensure_ascii=False)
            coupon_handler.send_coupon_to_user(user_id, coupon_id, 1, extend=coupon_extend)
            _LOGGER.info('sunday campaign, first returned back user %s, amount %s, total %s',
                user_id, first_return_amount, consume_amount)
        except Exception as e:
            _LOGGER.exception('sunday campaign first return exception, uid %s, %s', user_id, e)
    # start timer to return left amount 7 days later
    local_today = local_now().replace(hour=0, minute=0, second=0)
    execute_time = local_today + timedelta(7)
    execute_ts = int(time.mktime(local_to_utc(execute_time).timetuple()))
    event_msg = {
        'activity_id': activity_id,
    }
    TimerEvent.submit(TIMER_EVENT_TYPE.SUNDAY_RETURN, event_msg, execute_ts)


def return_second(activity_id):
    """
    第二次返还
    """
    _LOGGER.info('start second return back, %s', activity_id)
    records = sunday_db.get_records_by_activity(activity_id)
    for record in records:
        try:
            user_id = record.user_id
            total_amount = record.return_amount
            first_amount = record.first_amount
            second_amount = total_amount - first_amount
            sunday_db.update_second_record(record.id, second_amount)
            # send coupon
            coupon_index = second_amount - 1
            if coupon_index >= len(COUPON_RANGE):
                _LOGGER.error('sunday campaign, coupon index %s out of range', coupon_index)
                continue
            coupon_id = COUPON_RANGE[coupon_index]
            coupon_extend = {"add_by": "sunday_campaign", "activity_id": activity_id}
            coupon_extend = json.dumps(coupon_extend, ensure_ascii=False)
            coupon_handler.send_coupon_to_user(user_id, coupon_id, 1, extend=coupon_extend)
            _LOGGER.info('sunday campaign, second returned back user %s, amount %s, total %s',
                user_id, second_amount, total_amount)
        except Exception as e:
            _LOGGER.exception('sunday campaign second return exception, uid %s, %s', user_id, e)
