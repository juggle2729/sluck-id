# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

# add up one level dir into sys path

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import time
import random
import requests
from datetime import datetime

from luckycommon.model.virtual import VirtualPool
from luckycommon.db.activity import (get_activity, get_hot_activitys, get_latest_activitys, get_left_activitys)
from luckycommon.utils.weight import weight_sample

from django.conf import settings

_HOSTS = settings.ROOT_URL

_CREATE_USER_API = _HOSTS + '/api/v1/user/'
_LOGIN_API = _HOSTS + '/api/v1/user/login/'
_ACTIVITYS_API = _HOSTS + '/api/v1/activitys/?sort_id=1'
_BUY_API = _HOSTS + '/api/v2/activitys/%s/pay'

WHITE_LIST = [389, 399, 442]

account_list = []
last_ts = int(time.time())


def load_account_from_db():
    global account_list
    account_list = []
    accounts = VirtualPool.query.all()
    for account in accounts:
        account_list.append({
            'user_id': account.user_id,
            'token': account.token
        })


def choose_account():
    global last_ts
    now_ts = int(time.time())
    if now_ts - last_ts > 600:
        load_account_from_db()
        last_ts = now_ts
    if not account_list:
        load_account_from_db()
    return random.choice(account_list)


def need_virtual_buy(activity_id):
    activity = get_activity(activity_id)
    now = datetime.utcnow()
    passed_seconds = (now - activity.created_at).seconds
    if passed_seconds > 60:
        return True
    return False


def select_buy_info_latest(activity_dict):
    account = choose_account()
    target_amount = activity_dict['target_amount']
    unit = activity_dict['unit']

    seed = random.randint(1, 100)

    if seed < 20:
        r = 1
    elif seed < 30:
        r = random.randint(2, 5)
    elif seed < 40:
        r = random.randint(6, 10)
    elif seed < 50:
        r = random.randint(11, 20)
    elif seed < 60:
        r = random.choice([30, 40, 50, 60, 70, 80, 90, 100])
    elif seed < 70:
        r = random.randint(21, 99)
    elif seed < 80:
        r = random.choice([100, 150, 200, 250, 300, 350, 400, 450, 500])
    elif seed < 90:
        r = random.randint(101, 500)
    elif target_amount > 1000:
        r = random.randint(50, int(target_amount/10.0))
    else:
        r = 1000

    if r > target_amount / 3:
        if target_amount / 3 > 1:
            r = random.randint(target_amount / 4, target_amount / 3)
        else:
            r = 1

    if r > 10000:
        r = 1000

    if r % unit != 0:
        r = (r / unit) * unit

    if r > 100 and r % 10 > 0:
        r = (r / 10) * 10

    if r == 0:
        r = unit

    quantity = r
    if activity_dict['price'] == 0:
        quantity = 1
    return account['user_id'], account['token'], quantity


def choose_activity(activitys):
    weight = 100000
    count = len(activitys)
    diff = weight / count
    for activity in activitys:
        left_amount = activity['target_amount'] - activity['current_amount']
        activity['weight'] = weight + left_amount * 0.5
        if activity['price'] == 0:
            activity['weight'] += 20000
        if activity['unit'] > 1:
            update_weight = activity['weight'] - 200 * activity['unit']
            activity['weight'] = update_weight if update_weight > 0 else 1000
        weight -= diff
        if weight <= 0:
            weight = 1000
    candidates = [x for x in weight_sample(activitys, 1)]
    return candidates[0]


def monitor_activity():
    while True:
        rand_ts = random.randint(3, 15)
        time.sleep(rand_ts)
        activitys = get_available_activitys()
        if not activitys:
            print 'no available activity found, wait for next round...'
            continue
        activity = choose_activity(activitys)
        if need_virtual_buy(activity['id']):
            user_id, token, quantity = select_buy_info_latest(activity)
            res = buy(user_id, token, activity['id'], quantity)
            if res:
                print 'virtual buy done. user_id: %s, buy_amount: %s, total_amount: %s' % (user_id, quantity, activity['target_amount'])
        else:
            print 'no need to buy activity: %s' % (activity['id'])


def get_available_activitys():
    hot_activity_list, count = get_hot_activitys()
    latest_activity_list, count = get_latest_activitys()
    left_activity_list, count = get_left_activitys()
    choose_rand = random.randint(1, 10)
    if choose_rand <= 4:
        activity_list = latest_activity_list
    elif choose_rand <= 8:
        activity_list = hot_activity_list
    else:
        activity_list = left_activity_list
    return [activity.as_dict() for activity in activity_list]


def buy(user_id, token, activity_id, quantity):
    headers = {
        'X-AUTH-USER': user_id,
        'X-AUTH-TOKEN': token
    }
    pay_load = {
        'buy_quantity': quantity
    }
    api_path = _BUY_API % activity_id
    try:
        r = requests.post(api_path, data=pay_load, headers=headers)
        if r.status_code == 200:
            return r.text
        else:
            print 'buy failed'
            return None
    except Exception as e:
        print 'buy requests exceptions, %s' % e
        return None


if __name__ == "__main__":
    monitor_activity()
