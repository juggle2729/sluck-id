# -*- coding: utf-8 -*-
import logging

from luckycommon.cache import redis_cache
from luckyapi.logic import coupon as coupon_handler


_LOGGER = logging.getLogger('worker')

AMOUNT_CONDITION = 100
AWARD_AMOUNT = 1


def check_billboard(activity):
    if activity.buy_limit == 0 and activity.target_amount > AMOUNT_CONDITION:
        try:
            top_set = redis_cache.get_top_buyer(activity.id)
            stats_buy = redis_cache.get_stats_buy(activity.id)
            most_buyer = int(list(top_set)[0][0])
            first_buyer = int(stats_buy['first'])
            last_buyer = int(stats_buy['last'])
            # award
            user_set = set()
            user_set.add(most_buyer)
            user_set.add(first_buyer)
            user_set.add(last_buyer)
            for user_id in user_set:
                coupon_handler.send_coupon_to_user(user_id, 191, 1)
                _LOGGER.info('award billboard coupon to user %s for %s',
                    user_id, activity.id)
        except Exception as e:
            _LOGGER.exception('check billboard exception, %s', e)
