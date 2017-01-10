# -*- coding: utf-8 -*-
import json
import time

from django.conf import settings

from luckyapi.logic.crowdfunding import view_latest_activity
from luckycommon.cache import redis_cache
from luckycommon.model.activity import ACTIVITY_STATUS
from luckycommon.zero.db import zero as zero_db
from luckycommon.zero.model.zero import TEMPLATE_ID, TIME_CONF


def fill_timeline(current_index, status):
    timeline = []
    time_size = len(TIME_CONF)
    if status == ACTIVITY_STATUS.STARTED:
        current_index = (current_index - 1 + time_size) % time_size
    prev_index = (current_index - 1 + time_size) % time_size
    next_index = (current_index + 1 + time_size) % time_size
    for index, conf in enumerate(TIME_CONF):
        is_current = True if current_index  == index else False
        time_str = '%s:00' % conf['hour']
        if index < current_index:
            title = u'Hôm nay đã kết thúc'
        elif index == current_index:
            if status == ACTIVITY_STATUS.STARTED:
                title = u'Đang tiến hành'
            else:
                title = u'Sắp bắt đầu'
        else:
            title = u'Chưa bắt đầu'
        timeline.append({
            'is_current': is_current,
            'title': title,
            'time': time_str
        })
    return timeline


def get_zero_status(user_id):
    latest_lite = view_latest_activity(user_id, TEMPLATE_ID, lite_only=True)
    status = latest_lite['status']
    zero_dict = redis_cache.get_zero_time()
    if not zero_dict:
        return {}
    index = int(zero_dict['index'])
    ts = int(zero_dict['ts'])
    info = json.loads(zero_dict['info'])
    activity_name = info['name']
    cover = info['cover']
    template_id = int(zero_dict['template_id'])
    term_number = int(zero_dict['term_number'])
    countdown_ts = ts - int(time.time())
    if status == ACTIVITY_STATUS.STARTED:
        activity_name = latest_lite['goods']['name']
        cover = latest_lite['goods']['cover']
        template_id = TEMPLATE_ID
        term_number = latest_lite['term']
        countdown_ts = 0
    if countdown_ts < 0:
        countdown_ts = 0
    timeline = fill_timeline(index, status)
    data = {
        'status': status,
        'remain_ts': countdown_ts,
        'cmd': '11#%s/discovery/free_buy' % settings.WEB_APP_ROOT_URL,
        'gid': template_id,
        'term_number': term_number,
        'name': u'Mỗi ngày 0 đồng',
        'activity_name': activity_name,
        'cover': cover,
        'timeline': timeline
    }
    # check share times
    share_item = None if not user_id else zero_db.get_share(user_id, template_id, term_number)
    shared = True if share_item else False
    data.update({
        'shared': shared
    })
    # check zero push flag
    zero_push = None if not user_id else zero_db.get_push(user_id)
    need_push = False if not zero_push or zero_push.need_push == 0 else True
    data.update({
        'need_push': need_push
    })
    return data


def submit_share(user_id, template_id, term_number):
    if template_id == TEMPLATE_ID:
        zero_db.submit_share(user_id, template_id, term_number)


def set_push(user_id, push_open):
    zero_db.set_push(user_id, push_open)
