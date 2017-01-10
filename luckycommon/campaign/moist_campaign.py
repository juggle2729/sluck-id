# -*- coding: utf-8 -*-
import random
import logging
import time
from datetime import timedelta

from luckycommon.push import handler as push_handler

from luckycommon.campaign import valid_time

from luckycommon.model.coupon import COUPON_TYPE
from luckycommon.model.campaign import CAMPAIGN_TYPE, CAMPAIGN_DICT

from luckycommon.db.campaign import MoistCampaignDb

from luckycommon.timer import TIMER_EVENT_TYPE, TimerEvent

from luckycommon.utils.tz import local_now, local_to_utc


_LOGGER = logging.getLogger('lucky')

RECHARGE_PRICE = 50
AWARD_PRICE = 88


def calc_time(award_index):
    local_today = local_now().replace(hour=0, minute=0, second=0)
    weekday = local_today.date().weekday()
    if award_index == 0:
        return local_today + timedelta(1) 
    if award_index == 1:
        return local_today + timedelta(12 - weekday)
    if award_index == 2:
        return local_today + timedelta(19 - weekday)
    if award_index == 3:
        return local_today + timedelta(26 - weekday)
    if award_index == 4:
        return local_today + timedelta(33 - weekday)

AWARD_LIST = [{
        'time_desc': u'充值后次日',
        'coupon_list': [31, 36]
    },{
        'time_desc': u'充值后第二周的周六',
        'coupon_list': [32, 36]
    },{
        'time_desc': u'充值后第三周的周六',
        'coupon_list': [33, 36]
    },{
        'time_desc': u'充值后第四周的周六',
        'coupon_list': [34, 36]
    },{
        'time_desc': u'充值后第五周的周六',
        'coupon_list': [35, 36]
    }
]


def timer_to_award(user_id, campaign_id, campaign_info):
    push_handler.push_campaign_apply(user_id, campaign_info.get('title'), campaign_info.get('url'))
    award_index = 0
    for award_item in AWARD_LIST:
        execute_time = calc_time(award_index)
        execute_ts = int(time.mktime(local_to_utc(execute_time).timetuple()))
        event_msg = {
            'campaign_id': campaign_id,
            'user_id': user_id,
            'coupon_list': award_item['coupon_list']
        }
        TimerEvent.submit(TIMER_EVENT_TYPE.CAMPAIGN_AWARD, event_msg, execute_ts)
        award_index += 1


def add_new_recharge(user_id, price):
    try:
        _LOGGER.info('moist campaign add new recharge %s for user %s', price, user_id)
        for campaign_id,campaign_info in CAMPAIGN_DICT.items():
            if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
                continue
            if (campaign_info.get('type') == CAMPAIGN_TYPE.MOIST_CAMPAIGN
                and price >= RECHARGE_PRICE):
                    check_in = MoistCampaignDb.check_in(user_id, campaign_id, price, AWARD_PRICE)
                    if check_in:
                        # start timer to award
                        timer_to_award(user_id, campaign_id, campaign_info)
    except Exception as e:
        _LOGGER.exception('moist_campaign add recharge exception:%s', e)


def get_campaign_status(user_id, campaign_id):
    status = MoistCampaignDb.get_status(user_id, campaign_id)
    return 1 if status else 0
