# -*- coding: utf-8 -*-
import json
import logging
from luckycommon.utils.types import Enum
from luckycommon.cache import redis_cache
from luckycommon.utils import id_generator
from luckycommon.utils.exceptions import DataError
from future.utils import raise_with_traceback


_LOGGER = logging.getLogger(__name__)


TIMER_EVENT_TYPE = Enum({
    "ACTIVITY_EXPIRED": (0L, "actvity expired"),
    "ACTIVITY_NEXT": (2L, "start next activity"),
    "ACTIVITY_ANNOUNCE": (3L, "activity announce"),
    "ANNOUNCE_NOTIFY": (4L, "activity announce notify"),
    "COUPON_EXPIRED": (5L, "coupon expired"),
    "CAMPAIGN_AWARD": (6L, "coupon award for campaign"),  # 充值活动定时奖励
    "SHOW_NOTIFY": (7L, "show notify"),    # 提醒用户晒单
    "COUPON_NOTIFY": (8L, "coupon notify"),  # 提醒用户使用红包
    "SUNDAY_RETURN": (9L, "sunday campaign return coupon"),  # 周日活动返还红包
})


class TimerEvent(object):
    """
    Timer event wrapper 
    """
    def __init__(self, event_type, event_value, timestamp):
        self.event_type = event_type
        self.event_value = event_value  # must be a json dict, like {'id': xxxx, 'msg': xxxx}
        self.timestamp = timestamp

    @classmethod
    def submit(cls, event_type, event_msg, timestamp):
        # construct event_value dict
        event_value = {}
        uuid = id_generator.generate_uuid()
        event_value.update({'id': uuid})
        event_value.update({'msg': event_msg})
        try:
            cache_value = json.dumps(event_value)
            redis_cache.submit_timer_event(event_type, cache_value, timestamp)
        except Exception as e:
            _LOGGER.error('timer event submit error.(%s)' % e) 
            raise_with_traceback(DataError(e))

        return uuid
