# -*- coding: utf-8 -*-
import random
import logging

from luckycommon.campaign import valid_time, campaign_ts

from luckycommon.push import handler as push_handler

from luckycommon.model.campaign import CAMPAIGN_TYPE, CAMPAIGN_DICT, LEVEL_STATUS

from luckycommon.campaign.db import new_recharge_campaign as campaign_db
from luckycommon.account.db.account import get_account
from luckycommon.db.coupon import get_coupon_by_id

from luckycommon.utils.types import Enum
from luckycommon.utils.exceptions import ParamError, DataError


_LOGGER = logging.getLogger('worker')


LEVEL_LIST = [
    {
        'level': 6,
        'price': 5000,
        'coupon_conf': [185, 186, 187, 188, 189, 190],
        'double_ratio': 10,
        'coupon_numbers': 1,
    },
    {
        'level': 5,
        'price': 2000,
        'coupon_conf': [174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184],
        'double_ratio': 10,
        'coupon_numbers': 1,
    },
    {
        'level': 4,
        'price': 1000,
        'coupon_conf': [168, 169, 170, 171, 172, 173],
        'double_ratio': 15,
        'coupon_numbers': 1,
    },
    {
        'level': 3,
        'price': 500,
        'coupon_conf': [158, 159, 160, 161, 162, 163, 164, 165, 166, 167],
        'double_ratio': 15,
        'coupon_numbers': 1,
    },
    {
        'level': 2,
        'price': 200,
        'coupon_conf': [154, 155, 156, 157],
        'double_ratio': 20,
        'coupon_numbers': 1,
    },
    {
        'level': 1,
        'price': 50,
        'coupon_conf': [150, 151, 152, 153, 154],
        'double_ratio': 30,
        'coupon_numbers': 1,
    }
]


def add_new_recharge(user_id, price):
    try:
        _LOGGER.info('new recharge campaign add new recharge %s for user %s', price, user_id)
        for campaign_id, campaign_info in CAMPAIGN_DICT.items():
            if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
                continue
            if campaign_info.get('type') == CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN:
                campaign_title = campaign_info.get('title')
                for level_info in LEVEL_LIST:
                    if price >= level_info['price']:
                        # bingo
                        current_level = level_info['level']
                        campaign_db.add_new_level(user_id, campaign_id, current_level, price)
                        _LOGGER.info('%s reached new level %s in %s', user_id, current_level, campaign_id)
                        awarded_levels = campaign_db.get_award_levels(user_id, campaign_id)
                        if not awarded_levels:
                            push_handler.push_recharge_campaign_award(user_id, campaign_title)
                        break
    except Exception as e:
        _LOGGER.exception('new_recharge_campaign add recharge exception:%s', e)


def get_reached_levels(user_id, campaign_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if not campaign_info or campaign_info['type'] != CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN:
        raise ParamError('campaign id invalid')
    level_list = []
    available_levels = campaign_db.get_available_levels(user_id, campaign_id)
    available_dict = dict()
    for level in available_levels:
        available_dict.setdefault(level.level, 0)
        available_dict[level.level] += 1
    for level_info in LEVEL_LIST:
        level_id = level_info['level']
        if level_id in available_dict:
            level_list.append({
                'level': level_id,
                'quantity': available_dict[level_id],
                'status': LEVEL_STATUS.UNOPEN,
            })
        else:
            level_list.append({
                'level': level_id,
                'quantity': 0,
                'status': LEVEL_STATUS.UNREACHED,
            })
    return level_list


def _choose_coupon(tid_list):
    return random.choice(tid_list)


def activate_level(user_id, campaign_id, level_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if not campaign_info or campaign_info['type'] != CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN:
        raise ParamError('campaign id invalid')
    if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
        raise ParamError('campaign has expired')
    # activate
    level_items = campaign_db.get_levels(user_id, campaign_id, level_id)
    if not level_items:
        raise ParamError('level not reached')
    coupon_conf = None
    double_ratio = 0
    for level_info in LEVEL_LIST:
        level = level_info['level']
        if level == level_id:
            coupon_conf = level_info['coupon_conf']
            double_ratio = level_info['double_ratio']
            break
    if not coupon_conf:
        raise DataError('level not config')
    double_kill = False
    coupon_list = []
    for level_item in level_items:
        tid_list = []
        tid = _choose_coupon(coupon_conf)
        tid_list.append(tid)
        # 有x0%概率double
        if random.randint(1, 100) < double_ratio:
            double_kill = True
            tid_list.append(tid)
        c_list = campaign_db.award_level(level_item.id, user_id, tid_list)
        coupon_list.extend(c_list)
    return double_kill, coupon_list


def get_award_timeline(campaign_id):
    now_ts, start_ts, end_ts = campaign_ts(campaign_id)
    a_list = []
    items = campaign_db.get_award_timeline(campaign_id)
    for item in items:
        user_id = item.user_id
        coupon_id = item.coupons.split(',')[0]
        account = get_account(user_id)
        coupon = get_coupon_by_id(coupon_id)
        a_list.append({
            'user_id': user_id,
            'nick_name': account.nick_name,
            'coupon_title': coupon.title,
            'coupon_desc': coupon.desc
        })
    timeline_info = {
        'now_ts': now_ts,
        'start_ts': start_ts,
        'end_ts': end_ts,
        'list': a_list
    }
    return timeline_info


def query_tips(user_id):
    count = 0
    for campaign_id,campaign_info in CAMPAIGN_DICT.items():
        if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
            continue
        if campaign_info.get('type') == CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN:
            available_levels = campaign_db.get_available_levels(user_id, campaign_id)
            count += len(available_levels)
    return count
