# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import time
import tablib
import logging
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.activity import *
from luckycommon.model.strategy import *
from luckycommon.order.model.order import *
from luckycommon.db.account import get_account
from luckycommon.db.activity import get_activity
from luckycommon.stats import MG as mg
from luckycommon.cache import redis_cache
from luckycommon.model.pay import Pay
from luckycommon.utils.tz import utc_to_local, utc_to_local_str
from luckycommon.utils import id_generator


_LOGGER = logging.getLogger('worker')


def check(aid, fix=False):
    items = UserActivity.query.filter(UserActivity.activity_id == aid).all()
    activity = get_activity(aid)
    
    added_num = []
    lucky_numbers = range(1, activity.target_amount + 1)
    for item in items:
        user_id = item.user_id
        numbers = item.numbers.split(',')
        numbers = [int(num)-10000000 for num in numbers]
        added_num.extend(numbers)

    left_set = set(lucky_numbers) - set(added_num)
    pool_set = redis_cache.get_left_numbers(aid)
    pool_set = set([int(i) for i in pool_set])
    lost_set = left_set - pool_set
    if len(lost_set) > 0:
        print '%s lost %s amount:%s' % (aid, len(lost_set), activity.target_amount)
    if fix and len(lost_set) == 0:
        print 'right'

    left_num = list(lost_set)
    if fix and len(left_num) > 0:
        print 'ready to fix, %s' % (len(left_num))
        redis_cache.generate_numbers(aid, *left_num)
        print 'fixed %s' % aid


def get_active(uid):
    account = {}
    account['user_stats'] = mg.user_stats.find_one(
        {"_id": account_id}) or {}
    for k in 'updated_at', 'created_at':
        if k in account['user_stats']:
            account['user_stats'][k] = utc_to_local_str(
                account['user_stats'][k])
    active_count = mg.daily_stats.aggregate([
        {"$match": {"user_id": uid}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    account['active_days'] = active_count.next().get(
        'count', 0) if active_count.alive else 0
    return account


def check_a_group(uid, num_count):
    user_stats = redis_cache.get_user_stats(uid) or {}
    total_charge = int(user_stats.get('total_recharge', 0))
    total_win = int(user_stats.get('total_win', 0))
    if total_charge > 10000 and num_count > 100 and (total_win-total_charge < -2000):
        return True


def check_b_group(uid, num_count):
    user_stats = redis_cache.get_user_stats(uid) or {}
    total_charge = int(user_stats.get('total_recharge', 0))
    total_win = int(user_stats.get('total_win', 0))
    if total_charge > 10000 and num_count > 10 and (total_win-total_charge < -2000):
        return True



cmd = sys.argv[1]
if cmd == 'start':
    items = HotActivity.query.all() 
    for item in items:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (item.template_id, item.term_number))
        check(activity_id, fix=True)
if cmd == 'fix':
    """
    当某个商品号码缺失时，调用该工具进行号码池恢复
    """
    aid = sys.argv[2]
    check(aid, fix=True)
if cmd == 'fill':
    aid = sys.argv[2]
    a_list = [15385507, 15561068, 15283497, 15573806, 15634265, 15623112, 15669717, 15444491]
    b_list = [15385507, 15561068, 15283497, 15573806, 15634265, 15623112, 15669717, 15444491,
              15436176, 15254283, 15513781, 15672879, 15290843, 15346168, 15312349, 15544172, 15518721, 15402291, 15313690, 15288985, 15381723, 15568613, 15537688, 15168166]
    items = UserActivity.query.filter(UserActivity.activity_id == aid).all()
    a_numbers = []
    b_numbers = []
    a_group = []
    b_group = []
    for item in items:
        user_id = item.user_id
        nums = item.numbers.split(',')
        if check_a_group(user_id, len(nums)):
            a_group.append(user_id)
            a_numbers.extend(nums)
            print 'add %s to a list' % (user_id)
        if check_b_group(user_id, len(nums)):
            b_group.append(user_id)
            b_numbers.extend(nums)
            print 'add %s to b list' % (user_id)
    print len(a_numbers), len(b_numbers)
    print a_group, b_group
    item = LuckyNumber()
    item.activity_id = aid
    item.numbers = ','.join(a_numbers)
    item.option_numbers = ','.join(b_numbers)
    item.save()
if cmd == 'target':
    aid = sys.argv[2]
    items = UserActivity.query.filter(UserActivity.activity_id == aid).all()
    lucky_numbers = []
    v_list = []
    u_list = []
    count = 0
    for item in items:
        user_id = item.user_id
        nums = item.numbers.split(',')
        if user_id not in [16167315, 15056427, 15900110] and redis_cache.is_virtual_account(user_id):
            count += 1
            lucky_numbers.extend(nums)
        else:
            user_stats = redis_cache.get_user_stats(user_id) or {}
            total_charge = user_stats.get('total_recharge', 0)
            total_win = user_stats.get('total_win', 0)
            #active_data = get_active(user_id)
            data = {'uid': user_id, 'is_v': False, 'total_charge': total_charge,
                    'total_win': total_win, 'consume': len(nums)}
            u_list.append(data)
    lucky_numbers.sort(reverse=True)
    print len(lucky_numbers), count
    for u in u_list:
        print '%s\t%s\t%s\t%s\t%s' % (u['uid'], u['is_v'], u['total_charge'], u['total_win'], u['consume'])
    item = LuckyNumber()
    item.activity_id = aid
    item.numbers = ','.join(lucky_numbers)
    item.save()
if cmd == 'get_numbers':
    aid = sys.argv[2]
    items = LuckyNumber.query.filter(LuckyNumber.activity_id == aid).first()
    print len(items.numbers.split(','))
if cmd == 'scan_illegal':
    from luckycommon.order.model.order import AwardedOrder, Order, ORDER_STATUS, SHIP_STATUS
    from luckycommon.order.db.order import update_order
    from luckycommon.db.account import black_account
    from luckycommon.model.coupon import AccountCoupon
    TARGET_TIDS = [209,210,211,212,213,214,215,216,217,218,219]
    items = AwardedOrder.query.filter(
        AwardedOrder.status == ORDER_STATUS.WAIT_SHIP).all()
    for awarded_order in items:
        awarded_order = AwardedOrder.query.filter(AwardedOrder.order_id==awarded_order.order_id).one()
        aid = awarded_order.activity_id
        illegal_list = []
        items = Order.query.filter(Order.activity_id==aid).all()
        for item in items:
            extend = json.loads(item.extend)
            if 'coupon' in extend:
                coupon_id = int(extend['coupon'])
                coupon = AccountCoupon.query.filter(AccountCoupon.id == coupon_id).one()
                if coupon.template_id in TARGET_TIDS:
                    illegal_list.append(item.buyer)
        illegal_count = len(illegal_list)
        if awarded_order.user_id in illegal_list and float(illegal_count) / len(items) > 0.5:
            update_order(awarded_order, {
                'ship_status': SHIP_STATUS.ILLEGAL
            })
            black_account(awarded_order.user_id)
            _LOGGER.info('found illegal order, %s-%s', awarded_order.activity_id, awarded_order.activity_name)
        #print 'checked', awarded_order.activity_id
