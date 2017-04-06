# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.order.model.order import Order, OrderNumber
from luckycommon.cache import redis_cache
from luckycommon.model.activity import UserActivity, Activity


def put_numbers_back(activity_id):
    activity = Activity.query.filter(Activity.id == activity_id).first()
    lucky_numbers = range(1, activity.target_amount + 1)
    redis_cache.generate_numbers(activity.id, *lucky_numbers)
    uas = UserActivity.query.filter(UserActivity.activity_id == activity_id).all()
    uniques = []
    numbers = []
    for ua in uas:
        nums = ua.numbers.split(',')
        numbers += nums

    raw_numbers = [int(x) - 10000000 for x in numbers]
    uniques = list(set(raw_numbers))
    redis_cache.lock_numbers(activity_id, *raw_numbers)
    print len(raw_numbers), len(uniques)


# put_back('8157db8d-0473-35f9-8275-1ba0bce8e990')


def put_orders_back(activity_id):
    activity = Activity.query.filter(Activity.id == activity_id).first()
    orders = Order.query.filter(Order.activity_id == activity_id).all()
    if activity.winner:
        win_number = int(activity.winner)
    else:
        win_number = -1
    total_numbers = []
    for order in orders:
        order_id = order.id
        order_number = OrderNumber.query.filter(OrderNumber.order_id == order_id).first()
        if not order_number:
            print 'order number not found: %s' % order_id
            continue
        lucky_numbers = [int(x) for x in order_number.numbers.split(',')]
        total_numbers += lucky_numbers

    if total_numbers.count(win_number) > 1:
        print 'error, multiple win numbers'
    all_numbers = set(range(10000001, activity.target_amount + 10000001))
    unique_numbers = set(total_numbers)
    unused_numbers = all_numbers - unique_numbers
    print len(all_numbers), len(unique_numbers), len(unused_numbers)

    num_dict = {}
    for order in orders:
        order_id = order.id
        order_number = OrderNumber.query.filter(OrderNumber.order_id == order_id).first()
        if not order_number:
            print 'order number not found: %s' % order_id
            continue
        lucky_numbers = [int(x) for x in order_number.numbers.split(',')]
        for number in lucky_numbers:
            if number in all_numbers:
                all_numbers.remove(number)
                num_dict[number] = str(order.id)
            elif unused_numbers:
                number = unused_numbers.pop()
                num_dict[number] = str(order.id)
    print len(num_dict.keys()), sorted(num_dict.keys())[0], sorted(num_dict.keys())[-1]
    redis_cache.mapping_nums_with_order(activity_id, num_dict)

# put_orders_back('1ee7fd57-f5af-306d-9cbd-765c4ae0d2e0')
