# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.cache import redis_cache
from luckycommon.level.handler import get_user_level
from luckycommon.db import activity as activity_db
from luckycommon.utils.tz import now_ts

from django.conf import settings
from django.template import Context, Template
from django.utils.translation import ugettext as _


_LOGGER = logging.getLogger('lucky')

_MAX_COUNT = 10

_LIMIT_TS = 600


def _fill_delta_time(delta_ts):
    if delta_ts < 60:
        return _('seconds') % delta_ts
    elif delta_ts < 3600:
        return _('minutes') % (delta_ts / 60)
    else:
        return _('hours') % (delta_ts / 3600)


def _fill_text(text, params):
    """
    text: u'恭喜大白菜{{ time }}前获得iphone6s'
    params: {
        'ts': 1450789931
    }
    """
    template = Template(text)
    if params.get('ts'):
        delta_ts = now_ts() - int(params['ts'])
        params['time'] = _fill_delta_time(delta_ts)
    context = Context(params)
    return template.render(context)


def view_scrolling():
    """
    跑马灯
    """
    scrolling_list = []
    scrolling_set = redis_cache.range_scrolling()
    now = now_ts()
    count = 0
    for scrolling, ts in scrolling_set:
        if now - ts > _LIMIT_TS and count >= _MAX_COUNT:
            break
        scrolling_value = json.loads(scrolling)
        text = scrolling_value.get('text')
        params = scrolling_value.get('params')
        if params:
            text = _fill_text(text, params)
        cmd = scrolling_value.get('cmd')
        scrolling_list.append({
            'text': text,
            'cmd': cmd,
            'params': params
        })
        count += 1

    return scrolling_list


def view_lucky_wall():
    """
    幸运墙
    """
    wall_list = []
    scrolling_set = redis_cache.range_scrolling()
    now = now_ts()
    count = 0
    for scrolling, ts in scrolling_set:
        scrolling_value = json.loads(scrolling)
        text = scrolling_value.get('text')
        params = scrolling_value.get('params')
        delta_ts = now_ts() - int(params['ts'])
        if delta_ts < 60:
            time_ago = u'刚刚更新'
        elif delta_ts < 3600:
            time_ago = u'%s分钟前' % (delta_ts / 60)
        else:
            time_ago = u'%s小时前' % (delta_ts / 3600)
        wall_list.append({
            'time': time_ago,
            'uid': params.get('uid'),
            'nick_name': params.get('nick_name'),
            'avatar_id': params.get('avatar_id'),
            'activity_id': params.get('activity_id'),
            'activity_name': params.get('activity_name'),
            'cover': params.get('cover'),
            'pay_price': params.get('pay_price')
        })
        count += 1

    return wall_list


_HORN_LIMIT_TS = 120  # 取2分钟之内的
_HORN_AMOUNT_LEAST = 500
_HORN_RANGE = ((501, 1000), (1001, 2000),
               (2001, 3000), (3001, 4000),
               (4001, 5000), (5001, 6000),
               (6001, 10000),(10001, 5000000))


def _check_horn_index(amount):
    i = 0
    for r in _HORN_RANGE:
        if amount >= r[0] and amount <= r[1]:
            return i
        i += 1
    return -1


def view_horn():
    """
    大喇叭
    """
    horn_list = []
    scrolling_set = redis_cache.range_scrolling()
    now = now_ts()
    for scrolling, ts in scrolling_set:
        if now - ts > _HORN_LIMIT_TS:
            break
        scrolling_value = json.loads(scrolling)
        text = scrolling_value.get('text')
        params = scrolling_value.get('params')
        activity_id = params.get('activity_id')
        activity = activity_db.get_activity(activity_id, need_fill=False)
        horn_index = _check_horn_index(activity.target_amount)
        if -1 == horn_index:
            continue
        user_id = params.get('uid')
        nick_name = params.get('nick_name')
        level_dict = get_user_level(user_id)
        horn_list.append({
            'uid': user_id,
            'nick_name': params.get('nick_name'),
            'avatar_id': params.get('avatar_id'),
            'level': level_dict['current_level'],
            'level_icon': level_dict['level_icon'],
            'activity_name': params.get('activity_name'),
            'horn_index': horn_index
        })

    return horn_list
