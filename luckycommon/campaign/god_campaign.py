# -*- coding: utf-8 -*-
import random
import logging
from datetime import datetime

from luckycommon.model.campaign import GodCampaign
from luckycommon.model.strategy import StrategyPrivilege

from luckycommon.db.campaign import GodCampaignDb
from luckycommon.db import activity as activity_db
from luckycommon.db import strategy as strategy_db

from luckycommon.utils.exceptions import ParamError, DataError

from django.conf import settings


_LOGGER = logging.getLogger('lucky')


LEVEL_LIST = [
    {
        'level': 1,
        'direct_coupon_number': 1,
        'direct_ratio': [{
            'start': 1, 'end': 30, 'tid': 106,
        },{
            'start': 30, 'end': 55, 'tid': 107,
        },{
            'start': 55, 'end': 75, 'tid': 108,
        },{
            'start': 75, 'end': 90, 'tid': 109,
        },{
            'start': 90, 'end': 100, 'tid': 110,
        }]
    },
    {
        'level': 2,
        'condition_coupon_number': 1,
        'direct_coupon_number': 1,
        'condition_ratio': [{
            'start': 1, 'end': 30, 'tid': 52,
        },{
            'start': 30, 'end': 55, 'tid': 53,
        },{
            'start': 55, 'end': 75, 'tid': 54,
        },{
            'start': 75, 'end': 90, 'tid': 60,
        },{
            'start': 90, 'end': 100, 'tid': 61,
        }],
        'direct_ratio': [{
            'start': 1, 'end': 30, 'tid': 37,
        },{
            'start': 30, 'end': 55, 'tid': 38,
        },{
            'start': 55, 'end': 75, 'tid': 39,
        },{
            'start': 75, 'end': 90, 'tid': 40,
        },{
            'start': 90, 'end': 100, 'tid': 41,
        }]
    },
    {
        'level': 3,
        'condition_coupon_number': 2,
        'direct_coupon_number': 1,
        'condition_ratio': [{
            'start': 1, 'end': 30, 'tid': 55,
        },{
            'start': 30, 'end': 55, 'tid': 56,
        },{
            'start': 55, 'end': 75, 'tid': 57,
        },{
            'start': 75, 'end': 90, 'tid': 58,
        },{
            'start': 90, 'end': 100, 'tid': 59,
        }],
        'direct_ratio': [{
            'start': 1, 'end': 30, 'tid': 42,
        },{
            'start': 30, 'end': 55, 'tid': 43,
        },{
            'start': 55, 'end': 75, 'tid': 44,
        },{
            'start': 75, 'end': 90, 'tid': 45,
        },{
            'start': 90, 'end': 100, 'tid': 46,
        }]
    }
]


def get_campaign_status(user_id):
    now_time = datetime.utcnow()
    date_str = now_time.strftime('%Y-%m-%d')
    item = GodCampaignDb.get_status(user_id, date_str)
    return item


def _choose_coupon(ratio_list, count):
    tid_list = []
    for _ in range(count):
        rand_int = random.randint(1, 100)
        for ratio_item in ratio_list:
            if rand_int >= ratio_item['start'] and rand_int <= ratio_item['end']:
                tid_list.append(ratio_item['tid'])
                break
    return tid_list


def activate_level(user_id, level_id):
    now_time = datetime.utcnow()
    date_str = now_time.strftime('%Y-%m-%d')
    campaign_item = GodCampaignDb.get_status(user_id, date_str)
    if not campaign_item:
        raise DataError('campaign not applied')
    if level_id == 1:
        level_column = 'first_blood'
    elif level_id == 2:
        level_column = 'double_kill'
    elif level_id == 3:
        level_column = 'triple_kill'
    else:
        raise ParamError('level not exists')
    tid_list = []
    for level_info in LEVEL_LIST:
        level = level_info['level']
        if level == level_id:
            condition_number = level_info.get('condition_coupon_number')
            direct_number = level_info.get('direct_coupon_number')
            if condition_number and condition_number > 0:
                ratio_list = level_info.get('condition_ratio')
                tids = _choose_coupon(ratio_list, condition_number)
                tid_list.extend(tids)
            if direct_number and direct_number > 0:
                ratio_list = level_info.get('direct_ratio')
                tids = _choose_coupon(ratio_list, direct_number)
                tid_list.extend(tids)
            break
    if not tid_list:
        raise DataError('level not config')
    coupon_list = GodCampaignDb.activate(user_id, date_str, level_column, tid_list)
    _LOGGER.info('%s activate god campaign, level %s', user_id, level_id)
    return coupon_list


def get_privilege_tids(user_id, privilege_types):
    user_privileges = strategy_db.get_user_privileges(user_id)
    p_set = set()
    for user_privilege in user_privileges:
        if user_privilege.privilege_type in privilege_types:
            p_set.add(user_privilege.privilege_type)
    if not p_set:
        return []
    choosed_p = random.choice(list(p_set))
    min_amount, max_amount = StrategyPrivilege.range_price(choosed_p)
    candidate_tids = activity_db.get_tids_by_price(min_amount, max_amount)
    _LOGGER.info('%s got his privilege candidates, %s', user_id, candidate_tids)
    return candidate_tids


def fresh(user_id):
    # choose activity
    rand_int = random.randint(1, 100)
    if rand_int < 50:
        first_tid = random.choice(settings.GOD_TIDS)
    else:
        first_tids = get_privilege_tids(user_id, [1, 2])
        if not first_tids:
            first_tids = activity_db.get_tids_by_price(min_price=0, max_price=100)
        first_tid = random.choice(first_tids)
    second_tids = get_privilege_tids(user_id, [3, 4, 5])
    if not second_tids:
        rand_int = random.randint(1, 100)
        if rand_int < 40:
            second_tids = activity_db.get_tids_by_price(min_price=101, max_price=500)
        elif rand_int < 70:
            second_tids = activity_db.get_tids_by_price(min_price=501, max_price=1000)
        else:
            second_tids = activity_db.get_tids_by_price(min_price=1001, max_price=2000)
        if not second_tids:
            second_tids = activity_db.get_tids_by_price(min_price=0, max_price=2000)
    second_tid = random.choice(second_tids)
    third_tids = get_privilege_tids(user_id, [6, 7])
    if not third_tids:
        rand_int = random.randint(1, 100)
        if rand_int < 50:
            third_tids = activity_db.get_tids_by_price(min_price=2001, max_price=4000)
        else:
            third_tids = activity_db.get_tids_by_price(min_price=4001, max_price=100000)
        if not third_tids:
            third_tids = activity_db.get_tids_by_price(min_price=0, max_price=2000)
    third_tid = random.choice(third_tids)
    now_time = datetime.utcnow()
    date_str = now_time.strftime('%Y-%m-%d')
    new_item = GodCampaignDb.fresh(user_id, date_str, first_tid, second_tid, third_tid)
    _LOGGER.info('%s fresh his god campaign list', user_id)
    return new_item


def register(user_id, activity):
    """
    中奖之后的登记
    """
    template_id = activity.template_id
    now_time = datetime.utcnow()
    date_str = now_time.strftime('%Y-%m-%d')
    GodCampaignDb.register(user_id, date_str, template_id)


def query_tips(user_id):
    count = 0
    campaign_status = get_campaign_status(user_id)
    if campaign_status:
        if campaign_status.first_blood == 1:
            count += 1
        if campaign_status.double_kill == 1:
            count += 1
        if campaign_status.triple_kill == 1:
            count += 1
    return count
