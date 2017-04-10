# -*- coding: utf-8 -*-
import json
import random
import logging

from luckyapi.model.order import OrderRecord
from luckycommon.event import handler as event_handler

from luckycommon.cache import redis_cache
from luckycommon.cache.redis_lock import cache_lock

from luckycommon.credit.model.credit import AWARD_CREDIT_UNIT

from luckycommon.model.activity import ACTIVITY_STATUS

from luckycommon.async.async_job import (modify_hot_activity,
                                         virtual_buy_random,
                                         stats_recharge,
                                         stats_consume)

from luckycommon.order.db.order import OrderPayer
from luckycommon.account.db.account import get_account, get_online_info
from luckycommon.db import activity as activity_db
from luckycommon.db.coupon import get_coupon, use_coupon
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.zero.db import zero as zero_db

from luckycommon.utils import id_generator
from luckycommon.utils.exceptions import (ParamError,
                                          ResourceInsufficient,
                                          BalanceInsufficient)
from future.utils import raise_with_traceback


_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')


_LUCKY_NUMBER_MAX_TRY_COUNT = 1

_LUCKY_NUMBER_BASE = 10000000L

_ADJUST_LIMIT = 800  # 不能小于500


@cache_lock()
def generate_lucky_numbers(activity_id, choose_count):
    choosed_numbers = []
    # use latest way to generate numbers
    choosed_numbers = redis_cache.get_numbers(activity_id, choose_count)
    if choosed_numbers:
        redis_cache.lock_numbers(activity_id, *choosed_numbers)
    return choosed_numbers


def generate_pk_numbers(user_id, activity_id, choose_size):
    """
    pk场选号
    """
    return activity_db.choose_pk_numbers(user_id, activity_id, choose_size)


def revert_lucky_numbers(activity_id, revert_numbers):
    _LOGGER.info('revert lucky numbers %s for %s' %
                 (revert_numbers, activity_id))
    if len(revert_numbers) > 0:
        redis_cache.unlock_numbers(activity_id, *revert_numbers)


def check_complete(activity):
    # check if activity complete
    last_buy = False
    current_count = activity.target_amount - redis_cache.get_left_numbers_count(activity.id)
    if current_count >= activity.target_amount:
        last_buy = True
    return last_buy


def agent_random_pay(times=None):
    try:
        if not times:
            times = random.randint(1, 3)
        count = 0
        while count < times:
            # choose agent
            agent_id = redis_cache.get_random_virtual_account()
            # choose activity
            template_list = activity_db.get_cheap_template_ids()
            template_id = random.choice(template_list)
            latest_term = activity_db.get_latest_term(template_id)
            activity_id = id_generator.generate_uuid(
                'activity:%s:%s' % (template_id, latest_term))
            # fill context
            info = get_online_info(agent_id)
            extend = {} if not info.extend else json.loads(
                info.extend)
            order_context = {
                'ip': extend.get('ip'),
                'addr': extend.get('addr')
            }
            choosed_activity = activity_db.get_activity(activity_id)
            left_amount = choosed_activity.target_amount - choosed_activity.current_amount
            buy_quantity = choosed_activity.unit
            if buy_quantity >= left_amount:
                continue
            order, coupon = create_and_pay_order(agent_id, activity_id, buy_quantity, order_context)
            _LOGGER.info('agent %s random buy %s, %s', agent_id, activity_id, order.id)
            count += 1
    except Exception as e:
        _LOGGER.error('agent_random_pay exception, %s', e)


def adjust_buy_limit(user_id, activity):
    if activity.price == 0:
        # zero
        template_id = activity.template_id
        term_number = activity.term_number
        zero_share = zero_db.get_share(user_id, template_id, term_number)
        if zero_share:
            return activity.buy_limit + 1
        else:
            return activity.buy_limit
    else:
        return activity.buy_limit


def batch_create_and_pay_order(user_id, buy_list, total_price, extend):
    """
    批量创建并支付订单
    """
    total_amount = 0
    success_list = []
    fail_list = []
    coupon = None
    if extend.get('coupon'):
        coupon_id = extend['coupon']
        coupon = get_coupon(coupon_id, user_id)
    account = get_account(user_id)
    # check coupon
    if coupon:
        if total_price < coupon.price:
            _LOGGER.warn('total_price must ge coupon price')
            coupon = None
        elif (coupon.condition_price and 
              total_price < coupon.condition_price):
            _LOGGER.warn('buy quantity insufficient for coupon')
            coupon = None
        elif (coupon.condition_price and
              account.balance < coupon.condition_price - coupon.price):
            _LOGGER.warn('account balance insufficient for coupon')
            coupon = None
    # check balance sufficient
    if coupon and account.balance < total_price - coupon.price:
        _LOGGER.warn("account balance insufficient by coupon, %d < %d" %
                     (account.balance, total_price - coupon.price))
        raise BalanceInsufficient(
            "account balance insufficient by coupon, %d < %d" % (account.balance, total_price - coupon.price))
    if not coupon and account.balance < total_price:
        _LOGGER.warn("account balance insufficient, %d < %d" %
                     (account.balance, total_price))
        raise BalanceInsufficient(
            "account balance insufficient, %d < %d" % (account.balance, total_price))
    if coupon:
        # use coupon, fixme
        coupon_used = use_coupon(coupon)
        if not coupon_used:
            coupon = None
            del extend['coupon']
        else:
            _TRACKER.info({'user_id': coupon.user_id,
                           'coupon_id': coupon.id,
                           'type': 'use_coupon',
                           'target': buy_list,
                           'price': coupon.price})
    elif 'coupon' in extend:
        del extend['coupon']
    total_price = 0 # 实际总金额
    for buy_item in buy_list:
        activity_id = buy_item['activity_id']
        goods_quantity = buy_item['quantity']
        activity = activity_db.get_activity(activity_id, need_fill=False)
        if not activity or activity.status != ACTIVITY_STATUS.STARTED:
            continue
        # check quantity validation
        if goods_quantity <= 0 or goods_quantity % activity.unit != 0:
            continue
        if activity.buy_limit:
            continue
        # choose lucky number
        choosed_numbers = generate_lucky_numbers(activity_id, goods_quantity)
        if len(choosed_numbers) == 0:
            continue
        # ajust order price
        try:
            need_price = len(choosed_numbers) * activity.price  # 实际购买金额
            last_buy = check_complete(activity)
            need_adjust = True if (activity.target_amount > _ADJUST_LIMIT and
                                   last_buy) else False
            if need_adjust:
                # start async virtual buy
                # virtual_buy_random.delay(activity.id)
                agent_random_pay()
            order = single_buy(user_id, activity, choosed_numbers, need_price, extend, last_buy)
            buy_item['order'] = order
            data = {
                'activity_id': activity_id,
                'order': order,
            }
            success_list.append(data)
            total_price += need_price
        except Exception as e:
            fail_list.append(activity_id)
            revert_lucky_numbers(activity_id, choosed_numbers)
            _LOGGER.error('batch create order for %s fail, %s', activity_id, e)
            continue

    coupon_price = 0 if not coupon else coupon.price
    stats_consume.delay(user_id, total_price, coupon_price)
    return success_list, fail_list, coupon


def create_and_pay_order(user_id, activity_id, goods_quantity, extend):
    """
    创建并支付订单
    """
    # check activity validation
    activity = activity_db.get_activity(activity_id, need_fill=False)
    if not activity or activity.status != ACTIVITY_STATUS.STARTED:
        _LOGGER.warn(
            "create order fail. activity id(%s) invalid." % activity_id)
        raise ParamError("parameter `activity_id`(%s) invalid." % activity_id)
    if activity.pk and 'pk_size' not in extend:
        raise ParamError('pk_size invalid')

    # check quantity validation
    if goods_quantity <= 0 or goods_quantity % activity.unit != 0:
        _LOGGER.warn("order quantity invalid, %s is not integer times of %s" % (
            goods_quantity, activity.unit))
        raise ParamError("parameter `quantity`(%s) invalid." % goods_quantity)
    # check quantity limit
    activity.buy_limit = adjust_buy_limit(user_id, activity)
    if activity.buy_limit:
        user_activity = activity_db.get_user_activity(user_id, activity_id)
        if not user_activity or not user_activity.numbers:
            buyed_numbers = []
        else:
            buyed_numbers = user_activity.numbers.split(',')
        if len(buyed_numbers) + goods_quantity > activity.buy_limit:
            raise ResourceInsufficient(
                "buy limit (%s) reached." % activity.buy_limit)

    account = get_account(user_id)
    left_amount = activity.target_amount - activity.current_amount
    if goods_quantity > left_amount:
        goods_quantity = left_amount
    need_price = goods_quantity * activity.price
    # check coupon
    coupon = None
    if extend.get('coupon'):
        coupon_id = extend['coupon']
        coupon = get_coupon(coupon_id, user_id)
    if coupon:
        if need_price < coupon.price:
            _LOGGER.warn('need_price must ge coupon price')
            coupon = None
        elif (coupon.condition_price and 
              need_price < coupon.condition_price):
            _LOGGER.warn('buy quantity insufficient for coupon')
            coupon = None
        elif (coupon.condition_price and
              account.balance < coupon.condition_price - coupon.price):
            _LOGGER.warn('account balance insufficient for coupon')
            coupon = None

    # check balance sufficient
    if coupon and account.balance < need_price - coupon.price:
        _LOGGER.warn("account balance insufficient by coupon, %d < %d" %
                     (account.balance, need_price - coupon.price))
        raise BalanceInsufficient(
            "account balance insufficient by coupon, %d < %d" % (account.balance, need_price - coupon.price))
    if not coupon and account.balance < need_price:
        _LOGGER.warn("account balance insufficient, %d < %d" %
                     (account.balance, need_price))
        raise BalanceInsufficient(
            "account balance insufficient, %d < %d" % (account.balance, need_price))

    # choose lucky number
    if activity.pk:
        choose_size = int(extend['pk_size'])
        choosed_numbers = generate_pk_numbers(user_id, activity_id, choose_size)
    else:
        choosed_numbers = generate_lucky_numbers(activity_id, goods_quantity)
    if len(choosed_numbers) == 0:
        raise ResourceInsufficient("resource insufficient")
    # ajust order price
    need_price = len(choosed_numbers) * activity.price  # 实际购买金额
    if coupon:
        if need_price < coupon.price:
            coupon = None
            if account.balance < need_price:
                revert_lucky_numbers(activity.id, choosed_numbers)
                raise BalanceInsufficient(
                    "account balance insufficient, %d < %d" % (account.balance, need_price))
        else:
            try:
                # use coupon
                coupon_used = use_coupon(coupon)
                if not coupon_used:
                    coupon = None
                    del extend['coupon']
                else:
                    _TRACKER.info({'user_id': coupon.user_id,
                                   'coupon_id': coupon.id,
                                   'type': 'use_coupon',
                                   'target': activity.id,
                                   'price': coupon.price})
            except Exception as e:
                revert_lucky_numbers(activity.id, choosed_numbers)
                raise_with_traceback(e)
    elif 'coupon' in extend:
        del extend['coupon']

    last_buy = check_complete(activity)
    # adjust flag
    need_adjust = True if (last_buy and activity.target_amount > _ADJUST_LIMIT) else False
    if need_adjust:
        # start async virtual buy
        # virtual_buy_random.delay(activity.id)
        agent_random_pay()
    order = single_buy(user_id, activity, choosed_numbers, need_price, extend, last_buy)
    coupon_price = 0 if not coupon else coupon.price
    stats_consume.delay(user_id, need_price, coupon_price)
    return order, coupon


def single_buy(user_id, activity, choosed_numbers, need_price, extend, last_buy=False, need_adjust=False):
    try:
        # pay order
        save_numbers = [str(_LUCKY_NUMBER_BASE + int(num)) for num in choosed_numbers]
        order_record = OrderRecord()
        order_record.user_id = user_id
        order_record.activity_id = activity.id
        order_record.quantity = len(save_numbers)
        order_record.price = need_price
        order_record.lucky_numbers = save_numbers
        order_record.extend = extend

        buy_limit = activity.buy_limit
        order = OrderPayer.pay(order_record, buy_limit, need_adjust)
        # set first buyer
        redis_cache.set_first_buyer(activity.id, user_id)
    except Exception as e:
        revert_lucky_numbers(activity.id, choosed_numbers)
        raise_with_traceback(e)

    # pay success, save lucky numbers to redis for mapping order id
    num_dict = {}
    for num in save_numbers:
        num_dict[num] = str(order.id)
    # _LOGGER.info('#strategy# save number->order mappings, %s, %s' % (activity.id, len(num_dict.keys())))
    redis_cache.mapping_nums_with_order(activity.id, num_dict)

    if last_buy:
        _LOGGER.info(
            'activity %s has completed, ready to announce' % activity.id)
        ret = redis_cache.release_template_lock(activity.template_id)
        if not ret:
            # here, lock may be release by other session, just skip
            _LOGGER.warn('template lock has been released by other')
        # call timer event
        event_handler.call_announce_activity(activity.id, order.pay_at)
        event_handler.call_next_activity(activity.template_id)
        # set last buyer
        redis_cache.set_last_buyer(activity.id, user_id)

    # update HotActivity table for index
    modify_hot_activity(activity.id)
    order.lucky_numbers = ','.join(order_record.lucky_numbers)
    return order


def batch_pay(user_id, buy_list, order_context):
    success_list = []
    fail_list = []
    updated_buy_list = []
    total_price = 0
    # 从购物车取数量
    cart_dict = redis_cache.list_cart(user_id)
    for activity_id in buy_list:
        meta = cart_dict.get(activity_id)
        if not meta:
            continue
        meta = json.loads(meta)
        quantity = int(meta['number'])
        activity = activity_db.get_activity(activity_id)
        left_amount = activity.target_amount - activity.current_amount
        if quantity > left_amount:
            quantity = left_amount
        updated_buy_list.append({
            'activity_id': activity_id,
            'quantity': quantity
        })
        total_price += quantity * activity.price

    coupon = None
    if updated_buy_list:
        success_list, fail_list, coupon = batch_create_and_pay_order(user_id, updated_buy_list, total_price, order_context)
        for item in success_list:
            redis_cache.remove_cart(user_id, item['activity_id'])
            order = item['order']
            order_numbers = [] if not order.lucky_numbers else order.lucky_numbers.split(',')
            item.update({
                'order_id': order.id,
                'order_num_count': len(order_numbers),
                'order_numbers': order_numbers
            })
            del item['order']
            _TRACKER.info({'user_id': order.buyer, 'type': 'pay',
                           'activity_id': order.activity_id,
                           'price': order.total_price,
                           'from': order_context.get('from')})
    return success_list, fail_list, coupon


def pay_after_recharge(pay):
    # stats
    stats_recharge.delay(pay.id)
    # check if need to buy activity
    info = get_online_info(pay.user_id)
    extend = {} if not info.extend else json.loads(
        info.extend)
    order_context = {
        'pay_id': pay.id,
        'ip': extend.get('ip'),
        'addr': extend.get('addr')
    }
    extend = {} if not pay.extend else json.loads(pay.extend)
    if extend.get('coupon'):
        order_context.update({'coupon': extend['coupon']})
    order_context.update({'from': 'recharge'})

    if extend.get('buy_list'):
        try:
            buy_list = extend['buy_list']
            success_list, fail_list, coupon = batch_pay(pay.user_id, buy_list, order_context)
            refer_order_list = []
            # save refer order info into pay record
            valid_amount = 0
            for item in success_list:
                refer_order_list.append(item['order_id'])
                valid_amount += item['order_num_count']
            data = {'refer_order_list': refer_order_list}
            if coupon:
                data.update({'used_coupon': coupon.id})
                valid_amount -= coupon.price
            award_credit = valid_amount * AWARD_CREDIT_UNIT
            data.update({'award_credit': award_credit})
            update_pay_ext(pay.id, data)
        except Exception as e:
            _LOGGER.error(
                'automatic create_and_pay_order fail. %s' % e)
    elif pay.activity_id and pay.quantity:
        try:
            order_context.update({
                'pk_size': int(extend.get('pk_size', 0))
            })
            order, coupon = create_and_pay_order(
                pay.user_id, pay.activity_id, pay.quantity, order_context)
            # save refer order info into pay record
            data = {'refer_order_id': order.id}
            if coupon:
                data.update({'used_coupon': coupon.id})
            # check award credit
            award_credit = int(order.total_price) * AWARD_CREDIT_UNIT
            if coupon:
                award_credit = int(order.total_price - coupon.price) * AWARD_CREDIT_UNIT
            data.update({'award_credit': award_credit})
            update_pay_ext(pay.id, data)
            _TRACKER.info({'user_id': order.buyer, 'type': 'pay',
                           'activity_id': order.activity_id,
                           'price': order.total_price,
                           'from': 'recharge'})
        except Exception as e:
            _LOGGER.error(
                'automatic create_and_pay_order fail. %s' % e)
