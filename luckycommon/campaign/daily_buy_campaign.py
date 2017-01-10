# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from luckycommon.cache import redis_cache

from luckycommon.campaign import valid_time

from luckycommon.model.campaign import CAMPAIGN_TYPE, CAMPAIGN_DICT, LEVEL_STATUS

from luckycommon.db.campaign import DailyBuyCampaignDb
from luckycommon.db.coupon import get_group_coupon

from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.exceptions import ParamError


_LOGGER = logging.getLogger('lucky')


AMOUNT_UNIT = 10


def add_new_amount(user_id, amount):
    try:
        _LOGGER.info('add new amount %s for user %s', amount, user_id)
        for campaign_id,campaign_info in CAMPAIGN_DICT.items():
            if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
                continue
            if campaign_info.get('type') == CAMPAIGN_TYPE.DAILY_BUY_CAMPAIGN:
                now_time = datetime.strptime(utc_to_local_str(datetime.utcnow()), '%Y-%m-%d %H:%M:%S')
                date_str = now_time.strftime('%Y-%m-%d')
                DailyBuyCampaignDb.adjust_level(user_id, campaign_id, date_str, amount, amount_unit=AMOUNT_UNIT)
    except Exception as e:
        _LOGGER.exception('daily_buy_campaign, add_new_amount exception:%s', e)


def get_reached_levels(user_id, campaign_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if not campaign_info or campaign_info['type'] != CAMPAIGN_TYPE.DAILY_BUY_CAMPAIGN:
        raise ParamError('campaign id invalid')
    level_list = []
    now_time = datetime.strptime(utc_to_local_str(datetime.utcnow()), '%Y-%m-%d %H:%M:%S')
    date_str = now_time.strftime('%Y-%m-%d')
    items = DailyBuyCampaignDb.get_all_levels(user_id, campaign_id, date_str)
    current_amount = 0
    for item in items:
        if item.level == 0:
            current_amount = item.current_amount
            continue
        data = {
            'level': item.level,
            'status': item.status,
        }
        level_list.append(data)
        if item.current_amount > current_amount:
            current_amount = item.current_amount
    return current_amount, level_list


def activate_level(user_id, campaign_id, level_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if not campaign_info or campaign_info['type'] != CAMPAIGN_TYPE.DAILY_BUY_CAMPAIGN:
        raise ParamError('campaign id invalid')
    if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
        raise ParamError('campaign has expired')
    # activate
    now_time = datetime.strptime(utc_to_local_str(datetime.utcnow()), '%Y-%m-%d %H:%M:%S')
    date_str = now_time.strftime('%Y-%m-%d')
    level_item = DailyBuyCampaignDb.get_level(user_id, campaign_id, date_str, level_id)
    if not level_item or level_item.status == LEVEL_STATUS.UNREACHED:
        raise ParamError('level not reached')
    if level_item.status == LEVEL_STATUS.OPENED:
        group_coupon_id = level_item.coupon_id
        group_coupon = get_group_coupon(group_coupon_id)
        if not group_coupon:
            raise ParamError('level has expired')
        return group_coupon
    coupon = DailyBuyCampaignDb.award_level(user_id, campaign_id, date_str, level_id)
    return coupon


def query_tips(user_id):
    count = 0
    for campaign_id,campaign_info in CAMPAIGN_DICT.items():
        if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
            continue
        if campaign_info.get('type') == CAMPAIGN_TYPE.DAILY_BUY_CAMPAIGN:
            now_time = datetime.strptime(utc_to_local_str(datetime.utcnow()), '%Y-%m-%d %H:%M:%S')
            date_str = now_time.strftime('%Y-%m-%d')
            available_levels = DailyBuyCampaignDb.get_available_levels(user_id, campaign_id, date_str)
            count += len(available_levels)
    return count
