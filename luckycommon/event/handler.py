# -*- coding: utf-8 -*-
import json
import logging
import time
from datetime import datetime

from luckycommon.model import orm
from luckycommon.model.activity import Activity, ACTIVITY_STATUS

from luckycommon.cache import redis_cache

from luckycommon.utils.tz import now_ts, now_milli_ts
from luckycommon.third.lottery import calc_announce_delay
from luckycommon.timer import TIMER_EVENT_TYPE, TimerEvent

_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')

_DELAY_NEXT_SECONDS = 1
_BEFORE_ANNOUNCE_NOTIFY = 30
_DELAY_EXPIRE_SECONDS = 90 * 24 * 3600


def call_activity_expire(activity_id):
    event_msg = {'activity_id': activity_id}
    expire_ts = now_ts() + _DELAY_EXPIRE_SECONDS
    event_id = TimerEvent.submit(
        TIMER_EVENT_TYPE.ACTIVITY_EXPIRED, event_msg, expire_ts)
    _LOGGER.info(
        'start timer to expire activity in 90 days later. event id[%s]' % event_id)


def call_announce_notify(activity_id, notify_ts):
    """
    开奖20秒前通知用户
    """
    event_msg = {'activity_id': activity_id}
    event_id = TimerEvent.submit(
        TIMER_EVENT_TYPE.ANNOUNCE_NOTIFY, event_msg, notify_ts)
    _LOGGER.info('start timer to notify announce. event id[%s]' % event_id)


def call_next_activity(template_id, delay=_DELAY_NEXT_SECONDS):
    # call start next activity xxx minutes later
    event_msg = {'template_id': template_id}
    execute_time = now_ts() + delay
    event_id = TimerEvent.submit(
        TIMER_EVENT_TYPE.ACTIVITY_NEXT, event_msg, execute_time)
    _LOGGER.info('start timer to start next activity. event id[%s]' % event_id)


def call_announce_activity(activity_id, last_payat):
    # call async job to start announce logic
    event_msg = {
        'activity_id': activity_id,
        'last_payat': last_payat
    }
    ready_ts = now_ts()
    execute_ts = ready_ts + calc_announce_delay(activity_id)
    # update activity status
    try:
        ext = json.dumps({
            'announce_ts': execute_ts})
        Activity.query.filter(Activity.id == activity_id).update(
            {
                'status': ACTIVITY_STATUS.ANNOUNCE_READY,
                'extend': ext,
                'updated_at': datetime.utcnow(),
                'announced_at': datetime.fromtimestamp(execute_ts)
            })
        orm.session.commit()
        _LOGGER.info('call announce activity %s, lastpay %s', activity_id, last_payat)
    except Exception as e:
        _LOGGER.error('change activity status error, %s' % e)
        orm.session.rollback()
    finally:
        orm.session.close()

    announce_ts = now_milli_ts() + calc_announce_delay(activity_id) * 1000
    event_id = TimerEvent.submit(
        TIMER_EVENT_TYPE.ACTIVITY_ANNOUNCE, event_msg, announce_ts)
    _LOGGER.info('start timer to announce activity. event id[%s]' % event_id)
    # call announce notify
    notify_ts = execute_ts - _BEFORE_ANNOUNCE_NOTIFY
    call_announce_notify(activity_id, notify_ts)
    # 塞到cache队列中，用于加快开奖查询
    redis_cache.add_to_announce(activity_id)
