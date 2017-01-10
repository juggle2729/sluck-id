# -*- coding: utf-8 -*-
import random
import logging
from datetime import datetime

from luckycommon.campaign.model.fresh_wheel import *
from luckycommon.campaign.db import fresh_wheel as wheel_db

from luckycommon.cache import redis_cache
from luckycommon.db import account as account_db
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils import exceptions as err

from django.conf import settings


_LOGGER = logging.getLogger('lucky')


def _choose_award():
    rand_int = random.randint(1, 100)
    for ratio_item in AWARD_RATIO:
        if rand_int >= ratio_item['start'] and rand_int <= ratio_item['end']:
            return ratio_item['index'], ratio_item['coupon_tid'], ratio_item['desc']
    raise


def single_play(user_id):
    """
    转一次
    """
    user_stats = redis_cache.get_user_stats(user_id) or {}
    total_recharge = int(user_stats.get('total_recharge', 0))
    if not total_recharge:
        raise err.PermissionError('')
    award_index, coupon_tid, award_desc = _choose_award()
    award_coupon = wheel_db.play_wheel(user_id, coupon_tid, award_desc)
    _LOGGER.info('fresh wheel, %s awarded %s', user_id, award_coupon.template_id)
    return award_index, award_coupon


def get_status(user_id):
    item = wheel_db.get_wheel(user_id)
    user_stats = redis_cache.get_user_stats(user_id) or {}
    total_recharge = int(user_stats.get('total_recharge', 0))
    status = 0
    if not item:
        if total_recharge > 0:
            status = 1  # 已充值，未完成
        else:
            status = 0  # 未充值
    else:
        status = 2  # 已完成
    return status


def get_timeline():
    a_list = []
    items = wheel_db.get_award_timeline()
    uids = []
    for item in items:
        user_id = item.user_id
        coupon_id = item.coupon_id
        award_desc = item.award_desc
        uids.append(user_id)
        a_list.append({
            'user_id': user_id,
            'award_desc': award_desc,
        })
    accounts = account_db.get_account_in_ids(uids)
    accounts = dict([(account.id, account.nick_name) for account in accounts])
    for a in a_list:
        a['nick_name'] = accounts.get(a['user_id'])
    return a_list
