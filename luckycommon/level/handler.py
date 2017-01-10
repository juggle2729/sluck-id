# -*- coding: utf-8 -*-
import json
import logging
import copy

from datetime import datetime

from luckycommon.cache import redis_cache

from luckyapi.logic.coupon import send_coupon_to_user
from luckycommon.db import level as level_db
from luckycommon.account.db.account import get_account
from luckycommon.db.transaction import get_consume, get_award
from luckycommon.model.level import LEVEL_COUPON_STATUS
from luckycommon.push.handler import notify_level_up
from luckycommon.utils.week import iso_to_gregorian
from luckycommon.utils.tz import local_now

_LOGGER = logging.getLogger('lucky')

_LEVEL_SETTING = [
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v0.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v0.png', 'level': 0, 'level_name': 'level1',
     'need_exp': 0, 'coupon': 0},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v1.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v1.png', 'level': 1, 'level_name': 'level2',
     'need_exp': 1, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v2.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v2.png', 'level': 2, 'level_name': 'level3',
     'need_exp': 5, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v3.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v3.png', 'level': 3, 'level_name': 'level4',
     'need_exp': 20, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v4.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v4.png', 'level': 4, 'level_name': 'level5',
     'need_exp': 50, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v5.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v5.png', 'level': 5, 'level_name': 'level6',
     'need_exp': 200, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v6.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v6.png', 'level': 6, 'level_name': 'level7',
     'need_exp': 500, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v7.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v7.png', 'level': 7, 'level_name': 'level8',
     'need_exp': 2000, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v8.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v8.png', 'level': 8, 'level_name': 'level9',
     'need_exp': 5000, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v9.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v9.png', 'level': 9, 'level_name': 'level10',
     'need_exp': 10000, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v10.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v10.png', 'level': 10, 'level_name': 'level11',
     'need_exp': 50000, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v11.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v11.png', 'level': 11, 'level_name': 'level12',
     'need_exp': 100000, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v12.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v12.png', 'level': 12, 'level_name': 'level13',
     'need_exp': 500000, 'coupon': 3},
    {'level_icon_big': 'http://p.1yuan-gou.com/ic_big_level_v13.png',
     'level_icon': 'http://p.1yuan-gou.com/ic_level_v13.png', 'level': 13, 'level_name': 'level14',
     'need_exp': 1000000, 'coupon': 3},
]

_LEVEL_COUPON = [
    {'level': 0, 'coupon': [
    ]},
    {'level': 1, 'coupon': [
        {'template_id': 111, 'count': 1}
    ]},
    {'level': 2, 'coupon': [
        {'template_id': 112, 'count': 1}
    ]},
    {'level': 3, 'coupon': [
        {'template_id': 113, 'count': 1}
    ]},
    {'level': 4, 'coupon': [
        {'template_id': 114, 'count': 1}
    ]},
    {'level': 5, 'coupon': [
        {'template_id': 115, 'count': 1}
    ]},
    {'level': 6, 'coupon': [
        {'template_id': 116, 'count': 1}
    ]},
    {'level': 7, 'coupon': [
        {'template_id': 117, 'count': 1}
    ]},
    {'level': 8, 'coupon': [
        {'template_id': 116, 'count': 2},
        {'template_id': 117, 'count': 1}
    ]},
    {'level': 9, 'coupon': [
        {'template_id': 117, 'count': 5}
    ]},
    {'level': 10, 'coupon': [
        {'template_id': 117, 'count': 8}
    ]},
    {'level': 11, 'coupon': [
        {'template_id': 116, 'count': 10},
        {'template_id': 117, 'count': 10}
    ]},
    {'level': 12, 'coupon': [
        {'template_id': 117, 'count': 40}
    ]},
    {'level': 13, 'coupon': [
        {'template_id': 117, 'count': 80}
    ]},
]


def get_user_level(user_id):
    level = level_db.get_level(user_id)
    current_level = level.current_level if level else 0
    return {
        'current_level': current_level,
        'level_name': _LEVEL_SETTING[current_level]['level_name'],
        'level_icon': _LEVEL_SETTING[current_level]['level_icon'],
    }


def get_level_dict(user_id):
    level = level_db.get_level(user_id)
    if not level:
        level = init_level(user_id)
    exp = level.exp
    current_level = int(level.current_level)
    if current_level == len(_LEVEL_SETTING) - 1:
        exp_to_next_level = 0
    else:
        exp_to_next_level = _LEVEL_SETTING[current_level + 1]['need_exp'] - exp
    level_list = copy.deepcopy(_LEVEL_SETTING)
    coupon_status = json.loads(level.coupon_status)
    for k in coupon_status:
        level_list[int(k)]['coupon'] = coupon_status[k]
    return {
        'exp': exp,
        'current_level': current_level,
        'level_name': _LEVEL_SETTING[current_level]['level_name'],
        'level_icon': _LEVEL_SETTING[current_level]['level_icon'],
        'level_icon_big': _LEVEL_SETTING[current_level]['level_icon_big'],
        'exp_to_next_level': exp_to_next_level,
        'list': level_list
    }


def init_level(user_id):
    exp = calc_exp(user_id)
    current_level = calc_level_from_exp(exp)
    coupon_dict = {}
    coupon_dict['0'] = LEVEL_COUPON_STATUS.NOT_AVAILABLE
    for i in range(1, current_level + 1):
        coupon_dict[str(i)] = LEVEL_COUPON_STATUS.CAN_ACTIVATE
    coupon_status = json.dumps(coupon_dict)
    level = level_db.create_level(user_id, {'exp': exp,
                                            'current_level': current_level,
                                            'coupon_status': coupon_status})
    return level


def calc_exp(user_id):
    total_consume = get_consume(user_id)
    total_award = get_award(user_id)
    user = get_account(user_id)
    if not user or user.is_virtual:
        total_award = 0

    _LOGGER.info('consume: %s, award: %s', total_consume, total_award)
    if not total_consume:
        return 0
    if not total_award:
        total_award = 0
    total_consume = abs(total_consume)
    total_award = abs(total_award)
    return total_consume - total_award if total_consume - total_award > 0 else 0


def calc_level_from_exp(exp):
    i = 0
    while i < len(_LEVEL_SETTING) and exp >= _LEVEL_SETTING[i]['need_exp']:
        i += 1
    return i - 1


def add_exp(user_id, amount):
    if amount > 0:
        try:
            level = level_db.get_level(user_id)
            if not level:
                level = init_level(user_id)
            origin_exp = level.exp
            origin_level = calc_level_from_exp(origin_exp)
            coupon_dict = json.loads(level.coupon_status)
            new_exp = origin_exp + amount
            new_level = calc_level_from_exp(new_exp)
            for i in range(origin_level + 1, new_level + 1):
                coupon_dict[str(i)] = LEVEL_COUPON_STATUS.CAN_ACTIVATE
            if new_level > origin_level:
                notify_level_up(user_id, new_level, _LEVEL_SETTING[new_level]['level_name'])
            coupon_status = json.dumps(coupon_dict)
            level_db.update_level_with_dict(user_id, {
                'exp': new_exp,
                'current_level': new_level,
                'coupon_status': coupon_status})
            week_exp = get_week_exp(user_id)
            origin_week_exp = week_exp.exp
            new_week_exp = origin_week_exp + amount
            level_db.update_week_exp_with_dict(user_id, week_exp.year, week_exp.week_num, {
                'exp': new_week_exp
            })
            _LOGGER.info('add exp: %s %s', user_id, amount)
        except Exception as e:
            _LOGGER.exception('add exp exception, %s', e)


def get_week_exp(user_id):
    year, week_num, _ = datetime.now().isocalendar()
    week_exp = level_db.get_week_exp(user_id, year, week_num)
    if not week_exp:
        week_exp = level_db.create_week_exp(user_id, year, week_num)
    return week_exp


def is_coupon_available(user_id, level_num):
    level = level_db.get_level(user_id)
    if not level:
        return False
    coupon_dict = json.loads(level.coupon_status)
    if str(level_num) not in coupon_dict:
        return False
    if int(coupon_dict[str(level_num)]) != LEVEL_COUPON_STATUS.CAN_ACTIVATE:
        return False
    return True


def has_level_coupon(user_id):
    level = level_db.get_level(user_id)
    if not level:
        return False
    coupon_dict = json.loads(level.coupon_status)
    for k in coupon_dict:
        if int(coupon_dict[k]) == LEVEL_COUPON_STATUS.CAN_ACTIVATE:
            return True
    return False


def activate_coupon(user_id, level_num):
    # get coupon setting from level config
    level_coupon_config = _LEVEL_COUPON[int(level_num)]['coupon']
    # send coupon
    if len(level_coupon_config) > 0:
        level_db.activate_coupon(user_id, level_num, level_coupon_config)


def get_rank(count=10):
    items = level_db.get_top_level(count)
    rank_list = []
    for item in items:
        user_id = item.user_id
        account = get_account(user_id)
        avatar_id = account.avatar_id
        nickname = account.nick_name
        exp = item.exp
        current_level = item.current_level
        level_icon = _LEVEL_SETTING[current_level]['level_icon']
        level_name = _LEVEL_SETTING[current_level]['level_name']
        rank_list.append({
            'user_id': user_id,
            'avatar_id': avatar_id,
            'nickname': nickname,
            'exp': exp,
            'current_level': current_level,
            'level_icon': level_icon,
            'level_name': level_name,
        })
    return rank_list


def get_current_week_rank():
    year, week, _ = local_now().isocalendar()
    return get_week_rank(year, week)


def get_week_rank(year, week, count=10):
    # add cache
    cache_rank = redis_cache.get_cache_rank(year, week)
    if cache_rank:
        return json.loads(cache_rank)
    items = level_db.get_top_week_exp(year, week, count)
    rank_list = []
    for item in items:
        user_id = item.user_id
        account = get_account(user_id)
        avatar_id = account.avatar_id
        nickname = account.nick_name
        exp = item.exp
        level = level_db.get_level(user_id)
        current_level = level.current_level
        level_icon = _LEVEL_SETTING[current_level]['level_icon']
        level_name = _LEVEL_SETTING[current_level]['level_name']
        rank_list.append({
            'user_id': user_id,
            'avatar_id': avatar_id,
            'nickname': nickname,
            'exp': exp,
            'current_level': current_level,
            'level_icon': level_icon,
            'level_name': level_name,
        })
    redis_cache.set_cache_rank(year, week, json.dumps(rank_list, ensure_ascii=False))
    return rank_list


def get_week_rank_list():
    rank_list = []
    current_year, current_week, _ = datetime.now().isocalendar()
    for year_item in level_db.get_distinct_years():
        year = year_item[0]
        for week_item in level_db.get_distinct_weeks(year):
            week = week_item[0]
            top_user = get_top_user(year, week)
            start = iso_to_gregorian(year, week, 1)
            end = iso_to_gregorian(year, week, 7)
            if year != current_year or week != current_week:
                rank_list.append({
                    'year': year,
                    'week': week,
                    'start': start.strftime("%Y-%m-%d"),
                    'end': end.strftime("%Y-%m-%d"),
                    'top_user_avatar_id': top_user.avatar_id
                })
    return rank_list


def get_top_user(year, week):
    week_exp = level_db.get_top_week_exp(year, week, 1)[0]
    user_id = week_exp.user_id
    account = get_account(user_id)
    return account


def query_tips(user_id):
    result = has_level_coupon(user_id)
    return 1 if result else 0
