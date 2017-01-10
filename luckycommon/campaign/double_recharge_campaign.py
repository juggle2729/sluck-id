# -*- coding: utf-8 -*-
import random
import logging

from luckycommon.push import handler as push_handler

from luckycommon.model.campaign import CAMPAIGN_TYPE, CAMPAIGN_DICT, LEVEL_STATUS

from luckycommon.campaign import valid_time, campaign_ts
from luckycommon.campaign.model.double_recharge_campaign import *
from luckycommon.campaign.db import double_recharge_campaign as campaign_db


_LOGGER = logging.getLogger('worker')


LEVEL_LIST = [
    {
        'level': 5,
        'price': 2000,
        'coupon_conf': (250, 253), # (normal_tid, double_tid)
        'double_ratio': (15, 10),
    },
    {
        'level': 4,
        'price': 1000,
        'coupon_conf': (249, 252),
        'double_ratio': (10, 10),
    },
    {
        'level': 3,
        'price': 500,
        'coupon_conf': (248, 251),
        'double_ratio': (5, 10),
    },
    {
        'level': 2,
        'price': 100,
        'coupon_conf': (247, 247),
        'double_ratio': (0, 0),
    },
    {
        'level': 1,
        'price': 50,
        'coupon_conf': (246, 246),
        'double_ratio': (0, 0),
    },
]


def add_new_recharge(user_id, price):
    try:
        _LOGGER.info('double recharge campaign add new recharge %s for user %s', price, user_id)
        for campaign_id, campaign_info in CAMPAIGN_DICT.items():
            if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
                continue
            if campaign_info.get('type') == CAMPAIGN_TYPE.DOUBLE_RECHARGE_CAMPAIGN:
                campaign_title = campaign_info.get('title')
                for level_info in LEVEL_LIST:
                    if price >= level_info['price']:
                        # bingo
                        current_level = level_info['level']
                        level_item = campaign_db.add_new_level(user_id, campaign_id, current_level, price)
                        activate_level(user_id, campaign_id, level_item, level_info)
                        _LOGGER.info('%s reached new level %s in %s', user_id, current_level, campaign_id)
                        break
    except Exception as e:
        _LOGGER.exception('double_recharge_campaign add recharge exception:%s', e)


def activate_level(user_id, campaign_id, level_item, level_info):
    # activate
    a_tid, b_tid = level_info['coupon_conf']
    d_ratio, p_count = level_info['double_ratio']
    tid_list = [a_tid]
    rand = random.randint(1, 100)
    is_double = False
    if rand < d_ratio:
        level_count = campaign_db.get_level_count(user_id, campaign_id, level_item.level)
        if level_count >= p_count:
            tid_list = [b_tid]
            is_double = True
    c_list = campaign_db.award_level(level_item.id, user_id, tid_list, is_double)
    push_handler.push_double_campaign_award(user_id)
    _LOGGER.info('double recharge campaign, award %s to uid %s', tid_list, user_id)
