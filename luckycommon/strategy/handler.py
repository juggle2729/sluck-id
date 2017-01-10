# -*- coding: utf-8 -*-
import re
import logging
import random

from luckycommon.cache import redis_cache
from luckycommon.model.activity import ACTIVITY_STATUS
from luckycommon.account.db.account import get_account
from luckycommon.db.activity import get_activity, get_activity_users
from luckycommon.db import strategy as strategy_db
from luckycommon.order.db.order import get_order, get_last_valid_orders, get_activity_orders

from luckycommon.utils.tz import now_ts
from luckycommon.utils.exceptions import ParamError, AuthenticateError


_LOGGER = logging.getLogger('lucky')


def is_loser(user_id, current_consume, target_amount):
    user_stats = redis_cache.get_user_stats(user_id)
    if not user_stats:
        return False
    total_recharge = int(user_stats.get('total_recharge', 0))
    total_pay = float(user_stats.get('total_pay', current_consume))
    total_win = int(user_stats.get('total_win', 0))
    last_win = int(user_stats.get('last_win', 0))
    used_coupon = int(user_stats.get('used_coupon', 0))
    period = random.choice([4, 8, 12, 24, 36, 48])
    if now_ts() - last_win < 3600 * period:
        return False
    if float(total_recharge - used_coupon - total_win - target_amount)/total_recharge < 0.1:
        return False
    return True


def calc_result(activity):
    last_order, count = get_activity_orders(activity.id, limit=1)
    orders = get_last_valid_orders(last_order[0].pay_at)
    result_a = 0
    for order in orders:
        pay_at = order.pay_at
        account = get_account(order.buyer, use_cache=True)
        try:
            datas = re.split(r'[:,.]', pay_at.split(' ')[1])
            int_str = ''.join(datas)
            result_a += int(int_str)
        except Exception as e:
            _LOGGER.error('announce_activity split error %s' % e)
    lucky_number = result_a % activity.target_amount + 10000001L
    _LOGGER.info('calc result, activity_id:%s, lucky_number:%s' %
                 (activity.id, lucky_number))
    return lucky_number


def fetch_announce_result(activity_id):
    activity = get_activity(activity_id)
    if not activity:
        _LOGGER.error(
            'calc_result, activity %s not exists' % activity_id)
        raise ParamError('activity invalid')
    if activity.status != ACTIVITY_STATUS.ANNOUNCE_READY:
        _LOGGER.error(
            'calc_result, activity %s status invalid' % activity_id)
        raise ParamError('activity invalid')
    lucky_number = calc_result(activity)
    order_id = redis_cache.get_lucky_order(activity_id, lucky_number)
    order = get_order(order_id)
    winner_id = order.buyer
    winner_account = get_account(order.buyer)
    winner_number_count = 0
    virtual_accounts = redis_cache.get_virtual_account()
    user_activitys = get_activity_users(activity_id)
    v_list = []
    h_list = []
    loser_list = []
    for ua in user_activitys:
        user_id = ua.user_id
        nums = ua.numbers.split(',')
        nums = [long(num) for num in nums]
        if user_id == winner_id:
            winner_number_count = len(nums)
        if str(user_id) in virtual_accounts:
            v_list.append(user_id)
        else:
            h_list.append(user_id)
            if activity.target_amount < 500 and is_loser(user_id, len(nums), activity.target_amount):
                loser_list.append(user_id)
    virtual_win = True if str(winner_id) in virtual_accounts else False
    loser_win = True if winner_id in loser_list else False
    _LOGGER.info('activity:%s, v len:%s, h len:%s, loser len:%s' %
                 (activity_id, len(v_list), len(h_list), len(loser_list)))
    winner_stats = redis_cache.get_user_stats(winner_id) or {}
    data = {
        'uid': winner_id,
        'nick_name': winner_account.nick_name,
        'phone': winner_account.phone,
        'is_virtual': virtual_win,
        'is_loser': loser_win,
        'number_count': winner_number_count,
        'total_recharge': winner_stats.get('total_recharge', winner_number_count - 1),
        'total_win': winner_stats.get('total_win', 0),
        'last_win': winner_stats.get('last_win'),
        'loser_count': len(loser_list),
        'virtual_count': len(v_list),
        'human_count': len(h_list),
    }
    return data


def set_strategy_config(current_limit, current_manual_limit,
                        default_limit, default_manual_limit):
    if current_limit or current_manual_limit:
        strategy_db.set_current_limit(current_limit, current_manual_limit)
    if default_limit or default_manual_limit:
        strategy_db.set_strategy_config(default_limit, default_manual_limit)


def add_new_amount(user_id, amount):
    """
    for strategy privilege achievement system
    """
    try:
        _LOGGER.info(
            'add new amount %s for user %s in strategy sys', amount, user_id)
        # calc user net investment amount
        user_stats = redis_cache.get_user_stats(user_id) or {}
        total_pay = float(user_stats.get('total_pay', amount))
        total_win = int(user_stats.get('total_win', 0))
        latest_exp = total_pay - total_win
        strategy_db.adjust_privilege_level(user_id, latest_exp)
    except Exception as e:
        _LOGGER.exception('strategy add_new_amount exception:%s', e)


def add_special_privilege(user_id, recharge_amount):
    try:
        user_stats = redis_cache.get_user_stats(user_id) or {}
        total_recharge = int(user_stats.get('total_recharge', 0))
        if 0 == total_recharge and recharge_amount > 1:
            # 首充超过1元
            randint = random.randint(1, 100)
            if randint > 30:
                return
            count = redis_cache.get_daily_privilege()
            if count > 50:
                return
            strategy_db.add_special_privilege(user_id)
            _LOGGER.info('strategy add_special_privilege uid:%s', user_id)
    except Exception as e:
        _LOGGER.exception('strategy add_special_privilege exception:%s', e)
