# -*- coding: utf-8 -*-
import os
import sys

import re
import time
import json
import random
import logging
from copy import deepcopy
from datetime import datetime

from luckyapi.logic.crowdfunding import start_next_activity

from luckycommon.cache import redis_cache
from luckycommon.async.async_job import stats_announce, track_one, increment_user

from luckycommon.campaign import god_campaign

from luckycommon.lottery import internal_handler as lottery_handler

from luckycommon.model import orm
from luckycommon.order.model.order import Order
from luckycommon.order.db.order import get_order, get_last_valid_orders, Refunder
from luckycommon.db.goods import get_goods
from luckycommon.model.campaign import CAMPAIGN_DICT
from luckycommon.model.activity import ACTIVITY_STATUS, TEMPLATE_STATUS

from luckycommon.account.db.account import get_account, is_virtual_user
from luckycommon.db.coupon import expire_coupon, award_coupon
from luckycommon.db.activity import (get_activity, update_activity_status,
                                     get_user_activity, get_activity_users,
                                     update_template, ActivityStarter,
                                     update_ua_status, ActivityAnnouncer)
from luckycommon.db.strategy import (get_current_amount, add_current_amount,
                                     get_privilege_users, consume_privilege)

from luckycommon.push import PUSH_COMMANDS
from luckycommon.push import handler as push_handler
from luckycommon.strategy.handler import get_candidate_lucky_numbers, get_qualified_lucy_numbers
from luckycommon.sunday import callback as sunday_callback
from luckycommon.timer import TIMER_EVENT_TYPE, TimerEvent
from luckycommon.utils.tz import now_ts
from luckycommon.utils.exceptions import ResourceInsufficient, CacheError

from django.utils.translation import ugettext as _
from django.conf import settings

_LOGGER = logging.getLogger('worker')
_TRACKER = logging.getLogger('tracker')

_DELAY_CHECK_SECONDS = 3600


class EventHandler(object):
    """
    Abstract class
    """

    def process(self, event):
        raise NotImplementedError(
            'EventHandler class is supposed to an abstract class')


class AnnounceNotifyHandler(EventHandler):
    def process(self, event_msg):
        _LOGGER.info('start processing Announce Notify Event[%s]' % event_msg)
        try:
            activity_id = event_msg['activity_id']
            # update_ua_status(activity_id, ACTIVITY_STATUS.ANNOUNCE_READY)
            # TODO: use thread pool
            push_handler.push_revealing(activity_id)
        except Exception as e:
            _LOGGER.exception('AnnounceNotifyHandler process error.(%s)' % e)
        return True


class ActivityExpiredHandler(EventHandler):
    def process(self, event_msg):
        _LOGGER.info('start processing Activity Expired Event[%s]' % event_msg)
        try:
            activity_id = event_msg['activity_id']
            activity = get_activity(activity_id)
            if activity.status == ACTIVITY_STATUS.STARTED:
                _LOGGER.info('activity %s ready to expire' % activity_id)
                update_activity_status(activity_id, ACTIVITY_STATUS.EXPIRED)
                # refunding
                refunded_users = Refunder.refund(activity_id)
                try:
                    push_handler.push_refunding(activity_id, refunded_users)
                except Exception as e:
                    _LOGGER.exception(
                        'ActivityExpiredHandler push refunding error.(%s)' % e)

            return True
        except Exception as e:
            _LOGGER.exception('ActivityExpiredHandler process error.(%s)' % e)
            return False


class ActivityNextHandler(EventHandler):
    def process(self, event_msg):
        _LOGGER.info('start processing Activity Next Event[%s]' % event_msg)
        try:
            template_id = event_msg['template_id']
            start_next_activity(0, template_id)
        except CacheError as e:
            _LOGGER.exception(
                'ActivityNextHandler process cache error.(%s)' % e)
        except Exception as e:
            update_template(template_id, {'status': TEMPLATE_STATUS.PAUSED})
            _LOGGER.exception(
                'ActivityNextHandler process exception error.(%s)' % e)
        return True


class ActivityResumeHandler(EventHandler):
    def resume_activity(self, activity_id):
        activity = get_activity(activity_id, need_fill=False)
        if not activity:
            _LOGGER.error(
                'resume activity, but activity %s not exists' % activity_id)
            return
        try:
            activity = ActivityStarter.start(
                activity.template_id, activity.goods_id, activity)
        except Exception as e:
            _LOGGER.error('resume activity of (%s) error, %s' %
                          (activity.template_id, e))
            if isinstance(e, ResourceInsufficient):
                event_msg = {'activity_id': activity.id}
                execute_time = int(
                    time.mktime(datetime.utcnow().timetuple())) + _DELAY_CHECK_SECONDS
                event_id = TimerEvent.submit(
                    TIMER_EVENT_TYPE.ACTIVITY_RESUME, event_msg, execute_time)
                _LOGGER.info(
                    'start timer to check insufficient activity. event id[%s]' % event_id)
            else:
                raise e

    def process(self, event_msg):
        _LOGGER.info('start processing Activity Resume Event[%s]' % event_msg)
        try:
            activity_id = event_msg['activity_id']
            self.resume_activity(activity_id)
            return True
        except Exception as e:
            _LOGGER.exception('ActivityAnnounceHandler process error.(%s)' % e)
            return False


class ActivityAnnounceHandler(EventHandler):
    _MAX_TRY = 100
    _DEFAULT_RAND_LIMIT = 50  # 0 代表关闭
    _BASE_NUM = 10000001L
    _INTERNAL_SETTING = [
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 40000, 'NET': -0.1, 'DAILY_FREE': 0, 'FREE_NET': 20000},  # (40000
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 30000, 'NET': -0.5, 'DAILY_FREE': 0, 'FREE_NET': 16000},  # (30000, 40000]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 20000, 'NET': -1, 'DAILY_FREE': 0, 'FREE_NET': 10000},  # (20000, 30000]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 8000, 'NET': -1.5, 'DAILY_FREE': 1, 'FREE_NET': 4000},  # (12000, 20000]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 4000, 'NET': -2, 'DAILY_FREE': 1, 'FREE_NET': 2000},  # (8000, 12000]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 2000, 'NET': -3, 'DAILY_FREE': 2, 'FREE_NET': 1000},  # (4000, 8000]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 1000, 'NET': None, 'DAILY_FREE': 2, 'FREE_NET': 400},  # (2000, 4000]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 200, 'NET': None, 'DAILY_FREE': 5, 'FREE_NET': 100},  # (1000, 2000]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 40, 'NET': None, 'DAILY_FREE': 0, 'FREE_NET': 40},  # (240, 1000]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 4, 'NET': None, 'DAILY_FREE': 0, 'FREE_NET': 2},  # (100, 240]
        {'RAND_LIMIT': 0, 'SINGLE_BUY': 1, 'TOTAL_BUY': 2, 'NET': None, 'DAILY_FREE': 0, 'FREE_NET': 2},  # 100]
    ]
    # temporarily increase daily amount to 50000, origin 1000
    _DAILY_LIMIT = 50000

    def calc_result(self, orders, target_amount, lottery_number):
        result_a = 0
        result_b = int(lottery_number)
        a_list = []
        for order in orders:
            pay_at = order.pay_at
            # account = get_account(order.buyer, use_cache=True)
            try:
                datas = re.split(r'[:,.]', pay_at.split(' ')[1])
                int_str = ''.join(datas)
                result_a += int(int_str)
                a_list.append({
                    'time': pay_at,
                    'code': int_str,
                    # 'name': account.nick_name or 'Unknown',
                    'uid': order.buyer
                })
            except Exception as e:
                _LOGGER.error('announce_activity split error %s' % e)

        result = (result_a + result_b) % target_amount + \
                 ActivityAnnounceHandler._BASE_NUM
        return result, result_a, a_list

    def adjust_result(self, default_num, result_a, a_list, candidates, orders, target_amount):
        _LOGGER.info('#strategy# start adjusting')
        adjust_a = result_a
        b_list = deepcopy(a_list)
        candidates.sort(reverse=True)
        right_b = candidates[len(candidates) - 1]  # 先取最小的那个
        # 再看是否存在大于默认值且最接近的那个
        for n in candidates:
            if n > default_num:
                right_b = n
            else:
                break

        # 计算差值
        if right_b > default_num:
            delta_ms = right_b - default_num
        else:
            delta_ms = right_b + target_amount - default_num

        # 调整差值，从倒数第二个开始往下，只加不减
        adjust_a += delta_ms
        max_payat = int(b_list[0]['code'])  # 调整后的值不能超过该值
        last_order_time = redis_cache.get_last_order()
        last_order_time = 0 if not last_order_time else int(last_order_time)
        _LOGGER.info('#strategy# adjust result, right_b:%s delta_ms:%s last_order:%s max_payat:%s' %
                     (right_b, delta_ms, last_order_time, max_payat))
        max_ms_list = xrange(980, 998)
        adjust_ms_list = xrange(5, 20)
        for i, order in enumerate(orders):
            if i == 0:
                continue
            pay_at_code = int(b_list[i]['code'])
            pay_at_ms = pay_at_code % 1000  # 取毫秒部分
            if pay_at_code > last_order_time:
                if pay_at_ms + delta_ms >= 1000:  # 不能溢出
                    max_ms = random.choice(max_ms_list)
                    delta = max_ms - pay_at_ms
                else:
                    delta = delta_ms
                if delta <= 0:
                    continue
                if pay_at_code + delta > max_payat:
                    ms = random.choice(adjust_ms_list)
                    delta = max_payat - pay_at_code - ms
                    if delta < 0:
                        delta = 0
                pay_at_code += delta
                pay_at_code = str(pay_at_code)
                b_list[i]['code'] = (9 - len(pay_at_code)) * '0' + pay_at_code
                delta_ms -= delta  # 剩余的差值
                date_components = order.pay_at.split(' ')[0]
                time_components = '%s:%s:%s.%s' % (b_list[i]['code'][:2],
                                                   b_list[i]['code'][2:4],
                                                   b_list[i]['code'][4:6],
                                                   b_list[i]['code'][6:])
                new_pay_at = '%s %s' % (date_components, time_components)
                b_list[i]['time'] = new_pay_at
                Order.query.filter(Order.id == order.id).update(
                    {'pay_at': new_pay_at})
                _LOGGER.info('#strategy# consume delta %s,adjust order to new pay at[%s]',
                             delta, new_pay_at)
                if delta_ms == 0:
                    break
            else:
                break

        if delta_ms == 0:
            # success
            orm.session.commit()
            b_list.sort(key=lambda x: x.get('time'), reverse=True)
            _LOGGER.info(
                '#strategy# adjust result success, adjust_a:%s, target_amount:%s',
                adjust_a, target_amount)
            return True, right_b, adjust_a, b_list
        else:
            # fail
            orm.session.close()
            _LOGGER.info(
                '#strategy# adjust result fail, left delta:%s, target_amount:%s',
                delta_ms, target_amount)
            return False, default_num, result_a, a_list

    def load_strategy(self):
        # TODO: load strategy from db later
        self.internal_setting = ActivityAnnounceHandler._INTERNAL_SETTING
        self.daily_limit = ActivityAnnounceHandler._DAILY_LIMIT
        self.daily_amount = get_current_amount(self.daily_limit)
        self.virtual_accounts = redis_cache.get_virtual_account()

    def shoot_virtual(self, activity):
        need_virtual = False
        rand = random.randint(1, 100)
        rand_limit = ActivityAnnounceHandler._DEFAULT_RAND_LIMIT
        rand_list = self.internal_setting
        if activity.target_amount > 8000:
            rand_limit = rand_list[0]['RAND_LIMIT']
        elif activity.target_amount <= 8000 and activity.target_amount > 4000:
            rand_limit = rand_list[1]['RAND_LIMIT']
        elif activity.target_amount <= 4000 and activity.target_amount >= 2000:
            rand_limit = rand_list[2]['RAND_LIMIT']
        elif activity.target_amount <= 2000 and activity.target_amount >= 1000:
            rand_limit = rand_list[3]['RAND_LIMIT']
        elif activity.target_amount <= 1000 and activity.target_amount >= 240:
            rand_limit = rand_list[4]['RAND_LIMIT']
        elif activity.target_amount <= 240 and activity.target_amount >= 100:
            rand_limit = rand_list[5]['RAND_LIMIT']
        else:
            rand_limit = rand_list[6]['RAND_LIMIT']
        _LOGGER.debug('shoot virtual, rand:%s, rand_limit:%s',
                      rand, rand_limit)
        if rand <= rand_limit:
            need_virtual = True
            _LOGGER.info(
                '#strategy# <%s, %s>, rand: %s, rand_limit: %s' % (activity.template_id, activity.term_number, rand, rand_limit))

        if activity.template_id in settings.VIRTUAL_GOODS_IDS and rand < 20:
            need_virtual = True
            _LOGGER.info(
                '#strategy# <%s, %s>, virtual goods strategy applied' % (activity.template_id, activity.term_number))

        return need_virtual

    def standard_reached(self, activity, user_id, nums=None, ratio_check=True):
        candidates = []
        if not nums:
            ua = get_user_activity(user_id, activity.id)
            nums = ua.numbers.split(',')
        rand_list = self.internal_setting
        if activity.target_amount > 40000:
            interval_index = 0
        elif activity.target_amount <= 40000 and activity.target_amount > 30000:
            interval_index = 1
        elif activity.target_amount <= 30000 and activity.target_amount > 20000:
            interval_index = 2
        elif activity.target_amount <= 20000 and activity.target_amount > 12000:
            interval_index = 3
        elif activity.target_amount <= 12000 and activity.target_amount > 8000:
            interval_index = 4
        elif activity.target_amount <= 8000 and activity.target_amount > 4000:
            interval_index = 5
        elif activity.target_amount <= 4000 and activity.target_amount >= 2000:
            interval_index = 6
        elif activity.target_amount <= 2000 and activity.target_amount >= 1000:
            interval_index = 7
        elif activity.target_amount <= 1000 and activity.target_amount >= 240:
            interval_index = 8
        elif activity.target_amount <= 240 and activity.target_amount >= 100:
            interval_index = 9
        else:
            interval_index = 10

        single_buy_limit = rand_list[interval_index]['SINGLE_BUY']
        total_buy_limit = rand_list[interval_index]['TOTAL_BUY']
        net_ratio = rand_list[interval_index]['NET']
        if activity.price == 0:
            single_buy_limit = 1
            total_buy_limit = 2
            net_ratio = None
        # check total buy here
        user_stats = redis_cache.get_user_stats(user_id) or {}
        total_recharge = int(user_stats.get('total_recharge', 0))
        total_pay = float(user_stats.get('total_pay', len(nums)))
        total_win = int(user_stats.get('total_win', 0))
        if (len(nums) < single_buy_limit or total_pay < total_buy_limit or total_recharge < total_buy_limit - 1):
            _LOGGER.info(
                '#strategy# <%s, %s, %s>, len(nums): %s, single_buy_limit: %s, total_pay: %s, total_buy_limit: %s, total_recharge: %s' % (
                    activity.template_id, activity.term_number, user_id, len(nums), single_buy_limit, total_pay, total_buy_limit,
                    total_recharge))
            return False
        if net_ratio:
            user_net_ratio = float(total_recharge - total_win - activity.target_amount) / total_pay
            if user_net_ratio < net_ratio:
                _LOGGER.info(
                    '#strategy# <%s, %s, %s>, len(nums): %s, single_buy_limit: %s, total_pay: %s, total_buy_limit: %s, total_recharge: %s' % (
                        activity.template_id, activity.term_number, user_id, len(nums), single_buy_limit, total_pay, total_buy_limit,
                        total_recharge))
                return False
        # check illegal
        if total_recharge <= 0:
            if random.randint(1, 100) < 80:
                _LOGGER.info('#strategy# <%s, %s>,total_recharge: %s, random < 80' % (
                    activity.template_id, activity.term_number, total_recharge))
                return False
            elif total_win > 0:
                _LOGGER.info('#strategy# <%s, %s>,total_recharge: %s, total_win: %s' % (
                    activity.template_id, activity.term_number, total_recharge, total_win))
                return False
        if not ratio_check:
            _LOGGER.info('#strategy# detail <%s, %s>, ratio_check: %s' % (activity.template_id, activity.term_number, ratio_check))
            return True
        # check recharge amount ratio
        if activity.target_amount < 4000:
            _LOGGER.info('#strategy# <%s, %s>, activity.target_amount: %s' % (
                activity.template_id, activity.term_number, activity.target_amount))
            return True
        check_ratio = True
        ratio = random.randint(1, 100)
        user_net = total_recharge - total_win - activity.target_amount
        if user_net <= -50000 and ratio <= 50:
            check_ratio = False
        elif user_net > -50000 and user_net <= -40000 and ratio <= 50:
            check_ratio = False
        elif user_net > -40000 and user_net <= -20000 and ratio <= 45:
            check_ratio = False
        elif user_net > -20000 and user_net <= -15000 and ratio <= 45:
            check_ratio = False
        elif user_net > -15000 and user_net <= -10000 and ratio <= 40:
            check_ratio = False
        elif user_net > -10000 and user_net <= -6000 and ratio <= 40:
            check_ratio = False
        elif user_net > -6000 and user_net <= -4000 and ratio <= 30:
            check_ratio = False
        elif user_net > -4000 and user_net <= -2000 and ratio <= 30:
            check_ratio = False
        if not check_ratio:
            _LOGGER.info('#strategy# <%s, %s>, ratio_check: %s' % (activity.template_id, activity.term_number, ratio_check))
            _LOGGER.info('#strategy#, standard_reached check ratio fail, uid:%s, aid:%s', user_id, activity.id)
            return False
        return True

    def standard_reached_special(self, activity, user_id):
        rand_list = self.internal_setting
        if activity.target_amount > 40000:
            interval_index = 0
        elif activity.target_amount <= 40000 and activity.target_amount > 30000:
            interval_index = 1
        elif activity.target_amount <= 30000 and activity.target_amount > 20000:
            interval_index = 2
        elif activity.target_amount <= 20000 and activity.target_amount > 12000:
            interval_index = 3
        elif activity.target_amount <= 12000 and activity.target_amount > 8000:
            interval_index = 4
        elif activity.target_amount <= 8000 and activity.target_amount > 4000:
            interval_index = 5
        elif activity.target_amount <= 4000 and activity.target_amount >= 2000:
            interval_index = 6
        elif activity.target_amount <= 2000 and activity.target_amount >= 1000:
            interval_index = 7
        elif activity.target_amount <= 1000 and activity.target_amount >= 240:
            interval_index = 8
        elif activity.target_amount <= 240 and activity.target_amount >= 100:
            interval_index = 9
        else:
            interval_index = 10

        daily_free = rand_list[interval_index]['DAILY_FREE']
        free_net = rand_list[interval_index]['FREE_NET']
        today_free_dict = redis_cache.get_today_free_interval()
        today_free = int(today_free_dict.get(str(interval_index), 0))

        if daily_free <= today_free:
            _LOGGER.info('#strategy# <%s, %s, %s>, daily_free: %s, total_free: %s' % (
                activity.template_id, activity.term_number, user_id, daily_free, today_free))
            return False
        user_stats = redis_cache.get_user_stats(user_id) or {}
        total_recharge = int(user_stats.get('total_recharge', 0))
        total_win = int(user_stats.get('total_win', 0))
        user_net = total_recharge - total_win
        if user_net < free_net:
            _LOGGER.info('#strategy# <%s, %s, %s>, user_net: %s, free_net: %s' % (
                activity.template_id, activity.term_number, user_id, user_net, free_net))
            return False
        redis_cache.incr_today_free_interval(str(interval_index))
        _LOGGER.info('strategy daily free add uid:%s,aid:%s,amount:%s',
                     user_id, activity.id, activity.target_amount)
        _LOGGER.info('#strategy# <%s, %s, %s>, user_net: %s, free_net: %s' % (
            activity.template_id, activity.term_number, user_id, user_net, free_net))
        return True

    def reached_limit(self, current_price):
        # check daily limit
        if self.daily_amount.current_amount + current_price > self.daily_amount.amount_limit:
            _LOGGER.info('#strategy#, reached limit %s' % self.daily_amount.amount_limit)
            return True
        return False

    def reached_manual_limit(self, current_price):
        # check manual limit
        if self.daily_amount.manual_amount + current_price > self.daily_amount.manual_amount_limit:
            _LOGGER.info('reached manual limit %s' %
                         self.daily_amount.manual_amount_limit)
            return True
        return False

    def is_loser(self, user_id, current_consume, target_amount, p_conf):
        try:
            user_stats = redis_cache.get_user_stats(user_id)
            if not user_stats:
                return False
            total_recharge = int(user_stats.get('total_recharge', 0))
            total_pay = float(user_stats.get('total_pay', current_consume))
            total_win = int(user_stats.get('total_win', 0))
            last_win = int(user_stats.get('last_win', 0))
            used_coupon = int(user_stats.get('used_coupon', 0))
            period = random.choice(p_conf['interval'])
            _LOGGER.info('#strategy#, total_recharge %s, total_pay: %s, total_win: %s, last_win: %s, used_coupon: %s' % (
                total_recharge, total_pay, total_win, last_win, used_coupon))
            if now_ts() - last_win < 3600 * period / 4.0:
                _LOGGER.info('#strategy#, now_ts - last_win < 3600 * period')
                return False
            numerator = total_recharge if total_recharge > 0 else total_pay
            if float(total_recharge - used_coupon - total_win - target_amount) / numerator < p_conf['net']:
                _LOGGER.info(
                    '#strategy#, float(total_recharge - used_coupon - total_win - target_amount) / numerator < p_conf["net"]')
                return False
        except Exception as e:
            _LOGGER.exception('#strategy#, function is_loser exception, %s', e)
            return False
        return True

    def is_real(self, user_id):
        user_stats = redis_cache.get_user_stats(user_id) or {}
        total_recharge = int(user_stats.get('total_recharge', 0))
        return True if total_recharge > 0 else False

    def check_result(self, activity, lucky_number):
        virtual_win = False
        loser_win = False
        buy_all = False
        try:
            self.load_strategy()
            need_virtual = self.shoot_virtual(activity)
        except Exception as e:
            _LOGGER.error('shoot virtual exception, %s', e)
            need_virtual = True

        order_id = redis_cache.get_lucky_order(activity.id, lucky_number)
        order = get_order(order_id)
        _LOGGER.info('#strategy#, origin winner %s' % order.buyer)

        v_list = []
        loser_list = []
        real_list = []  # 真实付费用户号码列表
        # find privilege users
        try:
            privilege_users, p_conf = get_privilege_users(
                activity.target_amount)
        except Exception as e:
            _LOGGER.error('#strategy#, get privilege users exception, %s', e)
            privilege_users = []
            p_conf = {}
        _LOGGER.info('#strategy#, found %s privilege users', len(privilege_users))

        if str(order.buyer) in self.virtual_accounts:
            virtual_win = True

        user_activitys = get_activity_users(activity.id)
        for user_activity in user_activitys:
            nums = user_activity.numbers.split(',')
            nums = [long(num) for num in nums]
            user_id = user_activity.user_id
            if user_id == order.buyer:
                winner_ratio = len(nums) / float(activity.target_amount)
                if winner_ratio == 1:
                    buy_all = True
                if winner_ratio > 0.8:
                    _LOGGER.info('#strategy#, winner_ratio gt 0.8, skip adjust')
                    track_one.delay(collection='announce', properties={
                        'real_win': 1 if not virtual_win else 0,
                        'adjust': 0,
                        'winner_strategy': 0,
                        'loser_strategy': 0,
                        'buy_all': 1 if buy_all else 0,
                        'announce': 1,
                    })
                    return False, False, False, [], []

            if str(user_id) in self.virtual_accounts:
                v_list.extend(nums)
            elif user_id in privilege_users and self.is_loser(user_id, len(nums), activity.target_amount, p_conf):
                _LOGGER.info('found loser, %s', user_id)
                loser_list.extend(nums)
            try:
                if self.standard_reached(activity, user_id, nums=nums, ratio_check=False):
                    real_list.extend(nums)
            except Exception as e:
                _LOGGER.error('standard_reached exception, %s', e)

        if lucky_number in loser_list:
            loser_win = True
        # check loser
        if len(loser_list) >= 1:
            if activity.price == 0 and len(loser_list) > 0:
                need_loser = True
        elif len(loser_list) >= 1 and 'skip_ratio' not in p_conf:
            rand = random.randint(1, 100)
            # miss it by fifty percent
            if rand <= 50:
                loser_list = []
                _LOGGER.info('#strategy#, miss loser by ratio, %s', activity.id)
        need_loser = True if len(loser_list) > 0 else False
        need_adjust = False
        adjust_reason = ''
        first_candidates = []
        second_candidates = []
        if need_virtual and not virtual_win:
            need_adjust = True
            adjust_reason = u'赢家-自有中奖'
            if len(v_list) > 0:
                first_candidates = v_list
        elif not need_virtual and need_loser and not loser_win:
            if not self.reached_manual_limit(activity.target_amount):
                need_adjust = True
                adjust_reason = u'输家'
                if 'skip_ratio' in p_conf:
                    adjust_reason = u'输家a+'
                first_candidates = loser_list
                if not virtual_win and self.reached_limit(activity.target_amount):
                    if len(v_list) > 0:
                        second_candidates = v_list
            else:
                need_loser = False
        if not need_loser and not need_virtual and not virtual_win:
            try:
                limit_reached = self.reached_limit(activity.target_amount)
                basic_qualified = self.standard_reached(activity, order.buyer)
                # 检查每日放开策略
                if not basic_qualified and not self.standard_reached_special(activity, order.buyer):
                    need_adjust = True
                    adjust_reason = u'赢家-价格未达标'
                    rand = random.randint(1, 100)
                    if rand <= 0 and not limit_reached:
                        if len(real_list) > 0:
                            first_candidates = real_list
                            second_candidates = v_list
                            _LOGGER.info(
                                '#strategy#, standard not reached, try to send to real')
                        else:
                            first_candidates = v_list
                            second_candidates = real_list
                            _LOGGER.info(
                                '#strategy#, standard not reached, try to send to virtual')
                    else:
                        first_candidates = v_list
                        second_candidates = real_list
                else:
                    # shoot strategy of award limit by day
                    if limit_reached:
                        need_adjust = True
                        adjust_reason = u'赢家-超过每日限额'
                        if len(v_list) > 0:
                            first_candidates = v_list
            except Exception as e:
                _LOGGER.error('#strategy#, check standard reached exception, %s' % e)
                need_adjust = True
                adjust_reason = u'赢家-未知异常'
                first_candidates = v_list

        track_one.delay(collection='announce', properties={
            'real_win': 1 if not virtual_win else 0,
            'adjust': 1 if need_adjust else 0,
            'winner_strategy': 1 if u'赢家' in adjust_reason else 0,
            'loser_strategy': 1 if u'输家' in adjust_reason else 0,
            'buy_all': 1 if buy_all else 0,
            'announce': 1,
        })
        _LOGGER.info(
            '#strategy# <%s, %s>, winner:%s, need_virtual:%s, is_virtual:%s, need_loser:%s, is_loser:%s, need_adjust:%s, adjust_reason:%s',
            activity.template_id, activity.term_number, order.buyer, need_virtual, virtual_win, need_loser, loser_win, need_adjust,
            adjust_reason)
        return need_adjust, need_virtual, need_loser, first_candidates, second_candidates

    def announce_activity(self, activity_id, last_payat):
        activity = get_activity(activity_id, need_fill=False)
        if not activity:
            _LOGGER.error('announce activity, but activity %s not exists' % activity_id)
            return
        if activity.status != ACTIVITY_STATUS.ANNOUNCE_READY:
            _LOGGER.error('announce activity, but activity %s status invalid' % activity_id)
            return

        orders = get_last_valid_orders(last_payat)
        lottery = lottery_handler.get_latest_lottery()
        result, result_a, a_list = self.calc_result(orders, activity.target_amount, lottery.number)

        candidate_lucky_numbers = get_candidate_lucky_numbers(activity)
        adjust_success, result, result_a, a_list = self.adjust_result(result, result_a, a_list, candidate_lucky_numbers, orders,
                                                                      activity.target_amount)
        if not adjust_success:
            _LOGGER.info('#strategy# adjust failed, try use all qualified numbers')
            qualified_lucky_numbers = get_qualified_lucy_numbers(activity)
            adjust_success, result, result_a, a_list = self.adjust_result(result, result_a, a_list, qualified_lucky_numbers, orders,
                                                                          activity.target_amount)
        try:
            lucky_order_id = redis_cache.get_lucky_order(activity_id, result)
            lucky_order = ActivityAnnouncer.announce(
                activity, result, result_a, lottery, a_list, lucky_order_id)
            _LOGGER.info('#strategy# success, new winner:%s' % lucky_order.buyer)
            # remove lucky orders cache
            redis_cache.remove_lucky_order(activity_id)
            # 记录最大的pay at
            max_pay_at_code = int(a_list[0]['code'])
            redis_cache.set_last_order(max_pay_at_code)
            # push win
            try:
                self.spread(activity, lucky_order)
                god_campaign.register(lucky_order.buyer, activity)
                redis_cache.add_user_pending(lucky_order.buyer, 'award')
                if not is_virtual_user(lucky_order.buyer):
                    add_current_amount(activity.target_amount, lucky_order.buyer, False)
                # track
                track_info = {'user_id': lucky_order.buyer, 'type': 'win',
                              'activity_id': lucky_order.activity_id,
                              'activity_target': float(get_goods(
                                  activity.goods_id).price),
                              'activity_name': activity.name,
                              'term_number': activity.term_number}
                increment_user.delay(lucky_order.buyer, 'total_win', float(get_goods(activity.goods_id).price))
                track_one.delay(collection='win', properties={
                    'activity_id': lucky_order.activity_id,
                    'activity_target': float(get_goods(activity.goods_id).price),
                    'activity_name': activity.name,
                    'term_number': activity.term_number}, user_id=lucky_order.buyer)
                winned_activitys = redis_cache.get_winn_list(lucky_order.buyer)
                if len(winned_activitys) == 1:
                    cached_winner = redis_cache.get_activity_winner(
                        activity_id)
                    winner_info = json.loads(cached_winner)
                    track_info.update({
                        'first_win_cost': winner_info.get('num_count')
                    })
                _TRACKER.info(track_info)
                push_handler.push_win(
                    lucky_order.buyer, activity_id, lucky_order_id)
            except Exception as e:
                _LOGGER.exception(
                    'ActivityAnnounceHandler, finish work error.(%s)' % e)
            stats_announce.delay(activity_id, lucky_order.buyer)
        except Exception as e:
            _LOGGER.exception('announce_activity something wrong (%s)' % e)
            raise e

    def spread(self, activity, lucky_order):
        _SCROLLING_LIMIT = 20
        account = get_account(lucky_order.buyer)
        pay_price = int(lucky_order.total_price)
        ts = now_ts()
        command = '%d#%s' % (PUSH_COMMANDS.TO_ACTIVITY, activity.id)
        scrolling_dict = {
            # 'text': _('恭喜<font color="#2189ff">%s</font>{{ time }}前获得%s') % (account.nick_name, activity.name),
            #            'text': u"Selamat <font color='#2189ff'> %s </font> mendapatkan {{ time }} di menit %s" % (account.nick_name, activity.name),
            'text': u"<font color='#2189ff'> %s </font> berhasil tukar %s" % (account.nick_name, activity.name),
            'params': {
                'ts': ts,
                'uid': account.id,
                'nick_name': account.nick_name,
                'avatar_id': account.avatar_id,
                'activity_id': activity.id,
                'activity_name': activity.name,
                'cover': activity.cover or activity.images.split(',')[0],
                'pay_price': pay_price
            },
            'cmd': command
        }
        redis_cache.submit_scrolling(json.dumps(
            scrolling_dict, ensure_ascii=False), ts)
        # check to Trim
        if redis_cache.get_scrolling_count() > _SCROLLING_LIMIT:
            redis_cache.trim_scrolling()

    def process(self, event_msg):
        _LOGGER.info('start processing Activity Annouce Event[%s]' % event_msg)
        try:
            activity_id = event_msg['activity_id']
            last_payat = event_msg['last_payat']
            self.announce_activity(activity_id, last_payat)
            _TRACKER.info(
                {'activity_id': activity_id, 'type': 'announce_activity'})
            return True
        except Exception as e:
            _LOGGER.exception('ActivityAnnounceHandler process error.(%s)' % e)
            return False


class CouponExpiredHandler(EventHandler):
    def process(self, event_msg):
        _LOGGER.info('start processing Coupon Expired Event[%s]' % event_msg)
        try:
            coupon_id = event_msg['coupon_id']
            expire_coupon(coupon_id)
        except Exception as e:
            _LOGGER.exception('CouponExpiredHandler process error.(%s)' % e)
        return True


class ShowNotifyHandler(EventHandler):
    def process(self, event_msg):
        _LOGGER.info('start processing Show Notify Event[%s]' % event_msg)
        try:
            show_id = event_msg['show_id']
            push_handler.notify_show(show_id)
        except Exception as e:
            _LOGGER.exception('ShowNotifyHandler process error.(%s)' % e)
        return True


class CouponNotifyHandler(EventHandler):
    def process(self, event_msg):
        _LOGGER.info('start processing Coupon Notify Event[%s]' % event_msg)
        try:
            coupon_id = event_msg['coupon_id']
            push_handler.notify_coupon(coupon_id)
        except Exception as e:
            _LOGGER.exception('CouponNotifyHandler process error.(%s)' % e)
        return True


class CampaignAwardHandler(EventHandler):
    def process(self, event_msg):
        _LOGGER.info('start processing Campaign Award Event[%s]' % event_msg)
        try:
            campaign_id = event_msg['campaign_id']
            user_id = event_msg['user_id']
            coupon_list = event_msg['coupon_list']
            campaign_info = CAMPAIGN_DICT.get(campaign_id)
            if campaign_info:
                award_list = []
                for tid in coupon_list:
                    coupon = award_coupon(user_id, tid)
                    _LOGGER.info('award coupon %s to %s', tid, user_id)
                    _TRACKER.info({'user_id': coupon.user_id,
                                   'coupon_id': coupon.id,
                                   'type': 'create_coupon',
                                   'from': 'moist_campaign',
                                   'price': coupon.price})
                    award_list.append(coupon.desc)
                award_content = '+'.join(award_list)
                push_handler.push_campaign_award(
                    user_id, campaign_info.get('title'), award_content)
        except Exception as e:
            _LOGGER.exception('CampaignAwardHandler process error.(%s)' % e)
        return True


class SundayReturnHandler(EventHandler):
    def process(self, event_msg):
        _LOGGER.info('start processing Sunday Return Event[%s]' % event_msg)
        try:
            activity_id = event_msg['activity_id']
            sunday_callback.return_second(activity_id)
        except Exception as e:
            _LOGGER.exception('SundayReturnHandler process error.(%s)' % e)
        return True


if __name__ == "__main__":
    handler = ActivityAnnounceHandler()
    activity_id = sys.argv[1]
    last_payat = sys.argv[2]
    handler.announce_activity(activity_id, last_payat)
