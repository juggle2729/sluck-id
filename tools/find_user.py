# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.db.activity import get_activity,get_activity_users
from luckycommon.utils.tz import now_ts


def query_buy_ratio(activity_id):
    virtual_accounts = redis_cache.get_virtual_account()
    users = get_activity_users(activity_id)
    activity = get_activity(activity_id)
    v_list = []
    h_list = []
    v_amount = 0
    h_amount = 0
    for ua in users:
        user_id = ua.user_id
        nums = ua.numbers.split(',')
        nums = [long(num) for num in nums]
        if str(user_id) in virtual_accounts:
            v_list.append(user_id)
            v_amount += len(nums)
        else:
            h_list.append(user_id)
            h_amount += len(nums)
    print 'activity:%s, v len:%s, h len:%s, v amount:%s, h amount:%s' % (activity_id,
        len(v_list), len(h_list), v_amount, h_amount)
    count_ratio = float(len(v_list)) / len(h_list)
    amount_ratio = float(v_amount) / h_amount
    return (count_ratio, amount_ratio)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        activity_id = sys.argv[2]
        count_ratio, amount_ratio = query_buy_ratio(activity_id)
        print count_ratio, amount_ratio
