# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import time
import json
import logging
from datetime import datetime
from multiprocessing import Process
from luckycommon.cache import redis_cache
from luckycommon.cache.redis_lock import cache_lock

from luckycommon.timer import TIMER_EVENT_TYPE
from luckycommon.timer.handler import (ActivityExpiredHandler,
                                       ActivityResumeHandler,
                                       ActivityNextHandler,
                                       AnnounceNotifyHandler,
                                       CouponExpiredHandler,
                                       CampaignAwardHandler,
                                       ShowNotifyHandler,
                                       CouponNotifyHandler,
                                       SundayReturnHandler,
                                       ActivityAnnounceHandler)

from luckycommon.utils.tz import now_ts, now_milli_ts


_LOGGER = logging.getLogger('timer')

_DEFAULT_EVENT_HANDLERS = {
    TIMER_EVENT_TYPE.ACTIVITY_EXPIRED: ActivityExpiredHandler(),
    TIMER_EVENT_TYPE.ACTIVITY_NEXT: ActivityNextHandler(),
    TIMER_EVENT_TYPE.ACTIVITY_ANNOUNCE: ActivityAnnounceHandler(),
    TIMER_EVENT_TYPE.ANNOUNCE_NOTIFY: AnnounceNotifyHandler(),
    TIMER_EVENT_TYPE.COUPON_EXPIRED: CouponExpiredHandler(),
    TIMER_EVENT_TYPE.CAMPAIGN_AWARD: CampaignAwardHandler(),
    TIMER_EVENT_TYPE.SHOW_NOTIFY: ShowNotifyHandler(),
    TIMER_EVENT_TYPE.COUPON_NOTIFY: CouponNotifyHandler(),
    TIMER_EVENT_TYPE.SUNDAY_RETURN: SundayReturnHandler(),
}

_PROCESS_TIMEOUT = 30


class EventProcessor(object):
    """
    timer event processor
    """
    def __init__(self, event_type_list):
        self.event_type_list = event_type_list
        self.event_handlers = _DEFAULT_EVENT_HANDLERS
        self.infinite_process = True
        self.sleep_second = 1

    def get_expired_events(self, event_type):
        event_list = []
        try:
            if event_type == TIMER_EVENT_TYPE.ACTIVITY_ANNOUNCE:
                max_time = now_milli_ts()
            else:
                max_time = now_ts()
            value_list = redis_cache.range_expired_events(event_type, max_time)
            for event_value in value_list:
                event_list.append(event_value)
        except Exception as e:
            _LOGGER.exception('get_expired_events failed.(%s)' % e)

        return event_list

    def process(self, event_type):
        _LOGGER.info("begin processing timer event: %s" % TIMER_EVENT_TYPE.get_label(event_type))
        event_handler = self.event_handlers.get(event_type)
        if not event_handler:
            _LOGGER.error('event handler not found for %s(%s)' % (event_type,
                          TIMER_EVENT_TYPE.get_label(event_type)))
            return

        while self.infinite_process:
            events = self.get_expired_events(event_type)
            for event_value in events:
                try:
                    event_msg = json.loads(event_value)

                    # @cache_lock(lock_timeout=_PROCESS_TIMEOUT)
                    def handler_process(event_id):
                        success = event_handler.process(event_msg['msg'])
                        # remove timer key
                        redis_cache.remove_expired_event(event_type, event_value)
                        if not success:
                            # delay to activate this event
                            if event_type == TIMER_EVENT_TYPE.ACTIVITY_ANNOUNCE:
                                next_exec_time = now_milli_ts() + 30000
                            else:
                                next_exec_time = now_ts() + 30
                            redis_cache.submit_timer_event(event_type, event_value, next_exec_time)
         
                    handler_process(event_msg['id'])
                except Exception as e:
                    _LOGGER.error('event value invalid.(%s:%s) %s' % (event_type, event_value, e))

            if not events:
                time.sleep(self.sleep_second)

    def run(self):
        _LOGGER.info("timer processor run...")
        p_list = []
        for event_type in self.event_type_list:
            p = Process(target=self.process, args=(event_type,))
            p_list.append(p)
            p.start()

        for p in p_list:
            p.join()


if __name__ == "__main__":
    event_type_list = [k for k in TIMER_EVENT_TYPE.to_dict()]
    event_processor = EventProcessor(event_type_list)
    event_processor.run()
