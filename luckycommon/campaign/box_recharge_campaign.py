# -*- coding: utf-8 -*-
import random
import logging

from luckycommon.campaign import valid_time
from luckycommon.campaign.db import box_recharge_campaign as campaign_db
from luckycommon.model.campaign import CAMPAIGN_TYPE, CAMPAIGN_DICT
from luckycommon.utils import exceptions as err


_LOGGER = logging.getLogger('worker')


LEAST_PRICE = 50
LEVEL_DICT = {
    1: {
        'price': 50,
        'coupon_conf': [228, 229, 230, 231, 232],
        'coupon_numbers': 1,
    },
    2: {
        'price': 200,
        'coupon_conf': [232, 233, 234, 235],
        'coupon_numbers': 1,
    },
    3: {
        'price': 500,
        'coupon_conf': [236, 237, 238, 239, 240, 241, 242, 243, 244, 245],
        'coupon_numbers': 1,
    }
}


def add_new_recharge(user_id, price):
    try:
        _LOGGER.info('box recharge campaign add new recharge %s for user %s', price, user_id)
        for campaign_id, campaign_info in CAMPAIGN_DICT.items():
            if campaign_info.get('type') == CAMPAIGN_TYPE.BOX_RECHARGE_CAMPAIGN:
                if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
                    continue
                # bingo
                campaign_db.add_diamond(user_id, campaign_id, price)
                break
    except Exception as e:
        _LOGGER.exception('box_recharge_campaign add recharge exception:%s', e)


def get_balance(user_id, campaign_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if not campaign_info or campaign_info['type'] != CAMPAIGN_TYPE.BOX_RECHARGE_CAMPAIGN:
        raise err.ParamError('campaign id invalid')
    level_list = []
    diamond_item = campaign_db.get_diamond(user_id, campaign_id)
    return 0 if not diamond_item else diamond_item.balance


def _choose_coupon(tid_list):
    return random.choice(tid_list)


def activate_level(user_id, campaign_id, level_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if not campaign_info or campaign_info['type'] != CAMPAIGN_TYPE.BOX_RECHARGE_CAMPAIGN:
        raise err.ParamError('campaign id invalid')
    if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
        raise err.ParamError('campaign has expired')
    # activate
    level_conf = LEVEL_DICT.get(level_id)
    if not level_conf:
        raise err.ParamError('level invalid')
    coupon_conf = level_conf['coupon_conf']
    level_price = level_conf['price']
    coupon_list = []
    tid_list = []
    tid = _choose_coupon(coupon_conf)
    tid_list.append(tid)
    c_list = campaign_db.award_level(user_id, campaign_id, level_price, tid_list)
    coupon_list.extend(c_list)
    return coupon_list


def query_tips(user_id):
    count = 0
    for campaign_id,campaign_info in CAMPAIGN_DICT.items():
        if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
            continue
        if campaign_info.get('type') == CAMPAIGN_TYPE.BOX_RECHARGE_CAMPAIGN:
            diamond_item = campaign_db.get_diamond(user_id, campaign_id)
            if diamond_item and diamond_item.balance > LEAST_PRICE:
                count += 1
    return count
