# -*- coding: utf-8 -*-
import random
import logging

from luckycommon.cache import redis_cache

from luckycommon.campaign import valid_time

from luckycommon.model.coupon import COUPON_TYPE
from luckycommon.model.campaign import CAMPAIGN_TYPE, CAMPAIGN_DICT, LEVEL_STATUS

from luckycommon.db.campaign import RechargeCampaignDb

from luckycommon.utils.exceptions import ParamError, DataError
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.types import Enum
from luckycommon.utils.exceptions import ParamError


_LOGGER = logging.getLogger('lucky')

COUPON_SIZE = Enum({
    "SMALL": (1L, "small coupon"),           # 小红包 
    "BIG": (2L, "big coupon"),               # 大红包 
    "LARGE": (3L, "large coupon"),           # 超大红包 
    "XLARGE": (4L, "x large coupon"),        # 超超大红包 
})

COUPON_RATIO = {
    COUPON_SIZE.SMALL: [{
        'start': 1, 'end': 70, 'tid': 62,
    },{
        'start': 70, 'end': 100, 'tid': 63,
    }],
    COUPON_SIZE.BIG: [{
        'start': 1, 'end': 10, 'tid': 66,
    },{
        'start': 10, 'end': 20, 'tid': 67,
    },{
        'start': 20, 'end': 30, 'tid': 68,
    },{
        'start': 30, 'end': 43, 'tid': 69,
    },{
        'start': 43, 'end': 58, 'tid': 70,
    },{
        'start': 58, 'end': 73, 'tid': 71,
    },{
        'start': 73, 'end': 83, 'tid': 72,
    },{
        'start': 83, 'end': 91, 'tid': 73,
    },{
        'start': 91, 'end': 96, 'tid': 74,
    },{
        'start': 96, 'end': 99, 'tid': 75,
    },{
        'start': 100, 'end': 100, 'tid': 76,
    }],
    COUPON_SIZE.LARGE: [{
        'start': 1, 'end': 10, 'tid': 77 
    },{
        'start': 10, 'end': 20, 'tid': 78
    },{
        'start': 20, 'end': 35, 'tid': 79
    },{
        'start': 35, 'end': 55, 'tid': 80
    },{
        'start': 55, 'end': 70, 'tid': 81
    },{
        'start': 70, 'end': 80, 'tid': 82
    },{
        'start': 80, 'end': 90, 'tid': 83
    },{
        'start': 90, 'end': 95, 'tid': 84
    },{
        'start': 95, 'end': 98, 'tid': 85
    },{
        'start': 98, 'end': 100, 'tid': 86
    }],
    COUPON_SIZE.XLARGE: [{
        'start': 1, 'end': 25, 'tid': 144 
    },{
        'start': 25, 'end': 50, 'tid': 145
    },{
        'start': 50, 'end': 70, 'tid': 146
    },{
        'start': 70, 'end': 85, 'tid': 147
    },{
        'start': 85, 'end': 95, 'tid': 148
    },{
        'start': 95, 'end': 100, 'tid': 149
    }]
}


LEVEL_LIST = [
    {
        'level': 1,
        'price': 20,
        'coupon_size': COUPON_SIZE.SMALL, 
        'coupon_numbers': 1,
    },
    {
        'level': 2,
        'price': 50,
        'coupon_size': COUPON_SIZE.SMALL, 
        'coupon_numbers': 2,
    },
    {
        'level': 3,
        'price': 100,
        'coupon_size': COUPON_SIZE.SMALL, 
        'coupon_numbers': 5,
    },
    {
        'level': 4,
        'price': 200,
        'coupon_size': COUPON_SIZE.BIG, 
        'coupon_numbers': 1,
    },
    {
        'level': 5,
        'price': 400,
        'coupon_size': COUPON_SIZE.BIG, 
        'coupon_numbers': 2,
    },
    {
        'level': 6,
        'price': 800,
        'coupon_size': COUPON_SIZE.BIG, 
        'coupon_numbers': 5,
    },
    {
        'level': 7,
        'price': 1600,
        'coupon_size': COUPON_SIZE.LARGE, 
        'coupon_numbers': 1,
    },
    {
        'level': 8,
        'price': 3200,
        'coupon_size': COUPON_SIZE.LARGE, 
        'coupon_numbers': 2,
    },
    {
        'level': 9,
        'price': 6000,
        'coupon_size': COUPON_SIZE.LARGE, 
        'coupon_numbers': 5,
    },
    {
        'level': 10,
        'price': 10000,
        'coupon_size': COUPON_SIZE.XLARGE, 
        'coupon_numbers': 1,
    },
    {
        'level': 11,
        'price': 20000,
        'coupon_size': COUPON_SIZE.XLARGE, 
        'coupon_numbers': 2,
    },
    {
        'level': 12,
        'price': 50000,
        'coupon_size': COUPON_SIZE.XLARGE, 
        'coupon_numbers': 5,
    }
]


def add_new_recharge(user_id, price):
    try:
        _LOGGER.info('recharge campaign add new recharge %s for user %s', price, user_id)
        for campaign_id,campaign_info in CAMPAIGN_DICT.items():
            if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
                continue
            if campaign_info.get('type') == CAMPAIGN_TYPE.RECHARGE_CAMPAIGN:
                current_item = RechargeCampaignDb.get_current_level(user_id, campaign_id)
                current_level = current_item.level
                current_price = current_item.current_price + price
                # check next level
                for level_info in LEVEL_LIST:
                    if level_info['level'] <= current_level:
                        continue
                    if current_price >= level_info['price']:
                        # bingo
                        current_level = level_info['level']
                        RechargeCampaignDb.add_new_level(user_id, campaign_id, current_level, current_price)
                        _LOGGER.info('%s reached new level %s in %s', user_id, current_level, campaign_id)
                if current_level == current_item.level:
                    RechargeCampaignDb.update_current_level(user_id, campaign_id, current_level, current_price)
    except Exception as e:
        _LOGGER.exception('recharge_campaign add recharge exception:%s', e)


def get_reached_levels(user_id, campaign_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if not campaign_info or campaign_info['type'] != CAMPAIGN_TYPE.RECHARGE_CAMPAIGN:
        raise ParamError('campaign id invalid')
    level_list = []
    items = RechargeCampaignDb.get_all_levels(user_id, campaign_id)
    reached_dict = dict([(item.level, item) for item in items])
    current_price = 0
    if reached_dict:
        current_price = reached_dict[0].current_price 
    for level_info in LEVEL_LIST:
        level = level_info['level']
        if level in reached_dict:
            reached_item = reached_dict[level]
            data = {
                'level': level,
                'price': level_info['price'],
                'size': level_info['coupon_size'],
                'count': level_info['coupon_numbers'],
                'status': reached_item.status
            }
            level_list.append(data)
            if reached_item.current_price > current_price:
                current_price = reached_item.current_price
        else:
            level_list.append({
                'level': level,
                'price': level_info['price'],
                'size': level_info['coupon_size'],
                'count': level_info['coupon_numbers'],
                'status': LEVEL_STATUS.UNREACHED
            })
    return current_price, level_list


def _choose_coupon(ratio_list, count):
    tid_list = []
    for _ in range(count):
        rand_int = random.randint(1, 100)
        for ratio_item in ratio_list:
            if rand_int >= ratio_item['start'] and rand_int <= ratio_item['end']:
                tid_list.append(ratio_item['tid'])
                break
    return tid_list


def activate_level(user_id, campaign_id, level_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if not campaign_info or campaign_info['type'] != CAMPAIGN_TYPE.RECHARGE_CAMPAIGN:
        raise ParamError('campaign id invalid')
    if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
        raise ParamError('campaign has expired')
    # activate
    level_item = RechargeCampaignDb.get_level(user_id, campaign_id, level_id)
    if not level_item or level_item.status != LEVEL_STATUS.UNOPEN:
        raise ParamError('level not reached')
    tid_list = []
    for level_info in LEVEL_LIST:
        level = level_info['level']
        if level == level_item.level:
            coupon_size = level_info['coupon_size'] 
            count = level_info['coupon_numbers']
            ratio_list = COUPON_RATIO.get(coupon_size) 
            tid_list = _choose_coupon(ratio_list, count)
            break
    if not tid_list:
        raise DataError('level not config')
    coupon_list = RechargeCampaignDb.award_level(user_id, campaign_id, level_id, tid_list)
    return coupon_list


def query_tips(user_id):
    count = 0
    for campaign_id,campaign_info in CAMPAIGN_DICT.items():
        if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
            continue
        if campaign_info.get('type') == CAMPAIGN_TYPE.RECHARGE_CAMPAIGN:
            available_levels = RechargeCampaignDb.get_available_levels(user_id, campaign_id)
            count += len(available_levels)
    return count
