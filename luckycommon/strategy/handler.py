# -*- coding: utf-8 -*-
import re
import logging
import random

import datetime
import numpy
from sqlalchemy import func

from luckycommon.account.model.account import Account
from luckycommon.model import orm
from luckycommon.cache import redis_cache
from luckycommon.cache.redis_cache import get_accumulated_privilege_count, get_accumulated_privilege_amount, \
    increase_accumulated_privilege_count, increase_accumulated_privilege_amount
from luckycommon.db.strategy import get_current_amount
from luckycommon.model.activity import ACTIVITY_STATUS, Activity, UserActivity
from luckycommon.account.db.account import get_account, is_virtual_user
from luckycommon.db.activity import get_activity, get_activity_users, get_user_activity, get_user_activities, get_first_user_activity
from luckycommon.db import strategy as strategy_db
from luckycommon.order.db.order import get_order, get_last_valid_orders, get_activity_orders
from luckycommon.model.transaction import Transaction, TRANSACTION_TYPE, TRANSACTION_STATUS
from luckycommon.order.model.order import AwardedOrder

from luckycommon.utils.tz import now_ts
from luckycommon.utils.exceptions import ParamError, AuthenticateError

_LOGGER = logging.getLogger('worker')
_DEFAULT_DAILY_LIMIT = 50000
_MAX_PRIVILEGE_COUNT = 3
_MAX_PRIVILEGE_AMOUNT = 1500
_MIN_PRIVILEGE_BUY_RATIO = 0.3
_QUALIFIED_RANGE = [
    {'range': xrange(1, 50), 'single': 1, 'total': 2},
    {'range': xrange(50, 120), 'single': 1, 'total': 20},
    {'range': xrange(120, 1000), 'single': 5, 'total': 100},
    {'range': xrange(1000, 2000), 'single': 10, 'total': 500},
    {'range': xrange(2000, 4000), 'single': 50, 'total': 1000},
    {'range': xrange(4000, 6000), 'single': 100, 'total': 2000},
    {'range': xrange(6000, 10000), 'single': 200, 'total': 4000},
    {'range': xrange(10000, 15000), 'single': 200, 'total': 8000},
    {'range': xrange(15000, 20000), 'single': 500, 'total': 10000},
    {'range': xrange(20000, 10000000), 'single': 500, 'total': 15000},
]


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
    if float(total_recharge - used_coupon - total_win - target_amount) / total_recharge < 0.1:
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


def get_candidate_lucky_numbers(activity):
    candidate_win_users = get_candidate_win_users(activity)
    candidate_win_user = choose_win_user(candidate_win_users)
    candidate_lucky_numbers = get_user_numbers_in_activity(candidate_win_user, activity.id)
    _LOGGER.info('#strategy# candidate_lucky_numbers: %s' % candidate_lucky_numbers)
    return candidate_lucky_numbers


def get_user_numbers_in_activity(user_id, activity_id):
    _LOGGER.info('#strategy# user_id: %s, activity_id: %s' % (user_id, activity_id))
    user_activity = get_user_activity(user_id, activity_id)
    return [int(x) for x in user_activity.numbers.split(',')]


def get_candidate_win_users(activity):
    all_users_in_activity = get_all_users_in_activity(activity)
    virtual_users_in_activity = [int(x) for x in all_users_in_activity if is_virtual_user(x)]
    qualified_users_in_activity = [int(x) for x in all_users_in_activity if is_user_qualified(x, activity)]
    privilege_users_in_activity = [int(x) for x in qualified_users_in_activity if is_privilege_user(x, activity)]

    if is_overall_limit_reached(activity.target_amount):
        _LOGGER.info('#strategy# overall limit reached, virtual win. user_list: %s' % virtual_users_in_activity)
        if len(virtual_users_in_activity) == 0:
            _LOGGER.info('#strategy# overall limit reached, but virtual list empty. Fallback to fair race')
            return all_users_in_activity
        return virtual_users_in_activity

    if len(qualified_users_in_activity) < 1:
        _LOGGER.info('#strategy# no qualified user found, virtual win. user_list: %s' % virtual_users_in_activity)
        if len(virtual_users_in_activity) == 0:
            _LOGGER.info('#strategy# no qualified user found, but virtual list empty. Fallback to fair race')
            return all_users_in_activity
        return virtual_users_in_activity

    if len(privilege_users_in_activity) > 1:
        users_to_win = privilege_users_in_activity
        _LOGGER.info('#strategy# privilege users found, privilege win. user_list: %s' % users_to_win)
    else:
        users_to_win = list(set(qualified_users_in_activity + virtual_users_in_activity))
        _LOGGER.info('#strategy# privilege users not found, qualified & virtual win. user_list: %s' % users_to_win)

    if len(users_to_win) == 0:
        users_to_win = all_users_in_activity

    return users_to_win


def choose_win_user(candidate_win_users):
    probability_list = [get_user_weight(x) for x in candidate_win_users]
    probability_list = [float(x) / sum(probability_list) for x in probability_list]
    candidate_win_user = numpy.random.choice(candidate_win_users, p=probability_list)
    _LOGGER.info('#strategy# candidate_win_user: %s' % candidate_win_user)
    return candidate_win_user


def get_all_users_in_activity(activity):
    users = []
    user_activities = get_activity_users(activity.id)
    for user_activity in user_activities:
        users.append(user_activity.user_id)
    return users


def is_user_qualified(user_id, activity):
    numbers = get_user_numbers_in_activity(user_id, activity.id)
    single_buy = len(numbers)
    result = orm.session.query(func.sum(Transaction.price)).filter(Transaction.user_id == user_id).filter(
        Transaction.type == TRANSACTION_TYPE.BALANCE_BUY).filter(Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if result:
        total_pay = abs(float(result))
    else:
        total_pay = 0
    target_amount = activity.target_amount
    qualified_item = [x for x in _QUALIFIED_RANGE if target_amount in x['range']][0]
    single_qualification = qualified_item['single']
    total_qualification = qualified_item['total']
    if single_buy >= single_qualification and total_pay >= total_qualification:
        _LOGGER.info(
            '#strategy# user <%s> qualified. single: %s, total_pay: %s, target price: %s' % (user_id, single_buy, total_pay, target_amount))
        return True
    _LOGGER.info('#strategy# user <%s> is not qualified. single: %s, total_pay: %s, target price: %s' % (
        user_id, single_buy, total_pay, target_amount))


def is_privilege_user(user_id, activity):
    user_weight = get_user_weight(user_id)
    target_amount = activity.target_amount
    single_buy = len(get_user_numbers_in_activity(user_id, activity.id))
    accumulated_privilege_count = get_accumulated_privilege_count(user_id)
    accumulated_privilege_amount = get_accumulated_privilege_amount(user_id)
    if user_weight >= 1.2155 \
            and 100 <= target_amount <= 1000 \
            and single_buy >= target_amount * _MIN_PRIVILEGE_BUY_RATIO \
            and accumulated_privilege_count < _MAX_PRIVILEGE_COUNT \
            and accumulated_privilege_amount + target_amount < _MAX_PRIVILEGE_AMOUNT:
        _LOGGER.info('#strategy# user <%s> has privilege, target_amount: %s, single_buy: %s, privilege_count: %s, privilege_amount: %s' % (
            user_id, target_amount, single_buy, accumulated_privilege_count, accumulated_privilege_amount))
        increase_accumulated_privilege_count(user_id)
        increase_accumulated_privilege_amount(user_id, target_amount)
        return True
    _LOGGER.info('#strategy# user <%s> do not has privilege' % user_id)


def is_overall_limit_reached(target_amount):
    today_amount = get_current_amount(_DEFAULT_DAILY_LIMIT)
    if today_amount.current_amount + target_amount > today_amount.amount_limit:
        _LOGGER.info('#strategy# overall limit reached, current_amount: %s, amount_limit: %s, target_amount: %s' % (
            today_amount.current_amount, today_amount.amount_limit, target_amount))
        return True
    _LOGGER.info('#strategy# overall limit not reached, current_amount: %s, amount_limit: %s, target_amount: %s' % (
        today_amount.current_amount, today_amount.amount_limit, target_amount))


def get_user_weight(user_id):
    new_user = new_user_multiplier(user_id)
    first_buy_amount = first_buy_amount_multiplier(user_id)
    total_recharge = total_recharge_multiplier(user_id)
    relative_loss, absolute_loss = loss_multiplier(user_id)
    daily_first_buy = daily_first_buy_multiplier(user_id)
    daily_recharge = daily_recharge_multiplier(user_id)
    daily_loss = daily_loss_multiplier(user_id)
    first_5_buy = first_5_buy_multiplier(user_id)
    result = new_user * first_buy_amount * total_recharge * relative_loss * absolute_loss * daily_first_buy * daily_recharge * daily_loss * first_5_buy
    _LOGGER.info(
        "#strategy# user: %s weight: %s, new_user: %s first_buy_amount: %s  total_recharge: %s relative_loss: %s  absolute_loss: %s  daily_first_buy: %s  daily_recharge: %s  daily_loss: %s  first_5_buy: %s " % (
            user_id, result, new_user, first_buy_amount, total_recharge, relative_loss, absolute_loss, daily_first_buy, daily_recharge,
            daily_loss, first_5_buy))
    return result


def new_user_multiplier(user_id):
    account = get_account(user_id)
    register_at = account.created_at
    now = datetime.datetime.now()
    if now - register_at < datetime.timedelta(days=1):
        return 1.02
    if now - register_at < datetime.timedelta(days=2):
        return 1.01
    return 1


def first_buy_amount_multiplier(user_id):
    activity = get_first_user_activity(user_id)
    if len(activity.numbers) >= 10:
        return 1.02
    if len(activity.numbers) >= 2:
        return 1.01
    return 1


def total_recharge_multiplier(user_id):
    result = orm.session.query(func.sum(Transaction.price)).filter(Transaction.user_id == user_id).filter(
        Transaction.type == TRANSACTION_TYPE.IN).filter(Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if result:
        total_recharge = float(result)
    else:
        total_recharge = 0
    if total_recharge >= 10000:
        return 1.05
    if total_recharge >= 5000:
        return 1.02
    if total_recharge == 0:
        return 0.5
    return 1


def loss_multiplier(user_id):
    result = orm.session.query(func.sum(Transaction.price)).filter(Transaction.user_id == user_id).filter(
        Transaction.type == TRANSACTION_TYPE.IN).filter(Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if result:
        total_recharge = float(result)
    else:
        total_recharge = 0
    total_award = 0
    for award_result_dict in AwardedOrder.query.filter(AwardedOrder.user_id == user_id).all():
        activity = Activity.query.filter(Activity.id == award_result_dict.activity_id).first()
        if activity:
            total_award += activity.target_amount
    if total_recharge > 0:
        loss_rate = (total_recharge - total_award) / total_recharge
    else:
        loss_rate = 0
    loss = total_recharge - total_award
    relative = 1
    absolute = 1
    if loss_rate >= 0.5:
        relative = 1.02
    if loss_rate >= 0.8:
        relative = 1.03
    if loss_rate >= 1:
        relative = 1.05
    if loss >= 1000:
        absolute = 1.02
    if loss >= 5000:
        absolute = 1.03
    if loss >= 10000:
        absolute = 1.05
    return relative, absolute


def daily_first_buy_multiplier(user_id):
    activities = UserActivity.query.filter(
        UserActivity.created_at > datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).filter(
        UserActivity.user_id == user_id).all()
    if len(activities) == 1:
        return 1.02
    return 1


def daily_recharge_multiplier(user_id):
    result = orm.session.query(func.sum(Transaction.price)).filter(
        Transaction.updated_at > datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).filter(
        Transaction.user_id == user_id).filter(Transaction.type == TRANSACTION_TYPE.IN).filter(
        Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if result:
        daily_recharge = float(result)
    else:
        daily_recharge = 0
    if daily_recharge >= 10000:
        return 1.05
    if daily_recharge >= 5000:
        return 1.03
    if daily_recharge >= 1000:
        return 1.02
    if daily_recharge == 0:
        return 0.8
    return 1


def daily_loss_multiplier(user_id):
    result = orm.session.query(func.sum(Transaction.price)).filter(
        Transaction.updated_at > datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).filter(
        Transaction.user_id == user_id).filter(Transaction.type == TRANSACTION_TYPE.IN).filter(
        Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if result:
        daily_recharge = float(result)
    else:
        daily_recharge = 0
    daily_award = 0
    for award_result_dict in AwardedOrder.query.filter(AwardedOrder.user_id == user_id).filter(
                    AwardedOrder.updated_at > datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).all():
        activity = Activity.query.filter(Activity.id == award_result_dict.activity_id).first()
        if activity:
            daily_award += activity.target_amount

    loss = daily_award - daily_recharge
    if loss >= 5000:
        return 1.05
    if loss >= 2000:
        return 1.03
    if loss >= 1000:
        return 1.02
    return 1


def first_5_buy_multiplier(user_id):
    user_activities, _ = get_user_activities(user_id)
    if len(user_activities) < 5:
        return 1.02
    return 1
