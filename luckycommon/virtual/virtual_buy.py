# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import time
import json
import random
import requests
from datetime import datetime

from luckycommon.cache import redis_cache

from luckycommon.model.virtual import VirtualPool
from luckycommon.db.activity import (get_activity, get_activity_users, get_hot_activitys, get_hot_activitys_by_tids,
                                     get_costly_activitys, get_latest_activitys, get_left_activitys)
from luckycommon.utils.weight import weight_sample
from luckycommon.utils.tz import local_now

from django.conf import settings


_HOSTS = settings.ROOT_URL 

_CREATE_USER_API = _HOSTS + '/api/v1/user/'
_LOGIN_API = _HOSTS + '/api/v1/user/login/'
_ACTIVITYS_API = _HOSTS + '/api/v1/activitys/?sort_id=1'
_BUY_API = _HOSTS + '/api/v2/activitys/%s/pay'
_COLD_MIN = 1

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
    return random.choice(account_list)


def has_virtual_account_in(activity_id):
    activity_users = get_activity_users(activity_id)
    for u in activity_users:
        if redis_cache.is_virtual_account(u.user_id):
            return True, len(activity_users)

    return False, len(activity_users)


def need_virtual_buy(activity_id):
    activity = get_activity(activity_id)
    if activity.template_id in (774, 775):
        return False
    too_cold = False
    if (float(activity.current_amount) / activity.target_amount) < _COLD_MIN:
        too_cold = True
    now = datetime.utcnow()
    passed_seconds = (now - activity.created_at).seconds
    if passed_seconds > 30 and too_cold:
        return True

    return False


def select_buy_info_latest(activity_dict, diaosi):
    account = choose_account()
    template_id = activity_dict['template_id']
    target_amount = activity_dict['target_amount']
    current_amount = activity_dict['current_amount']
    left_amount = target_amount - current_amount
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
        r = random.choice([30,40,50,60,70,80,90,100])
    elif seed < 70:
        r = random.randint(21, 99)
    elif seed < 80:
        r = random.choice([200,300,400,500,600,700,800,900,1000])
    elif seed < 90:
        r = random.randint(101, 999)
    elif target_amount > 1000:
        r = random.randint(1000, target_amount)
    else:
        r = 1000

    if diaosi:
        if target_amount < 200:
            r = random.randint(1, 10)
        else:
            r = random.randint(1, 50)

    if r > target_amount/3:
        if target_amount/3 > 1:
            r = random.randint(target_amount/4, target_amount/3)
        else:
            r = 1

    if r > 10000:
        r = 1000

    if r % unit != 0:
        r = (r/unit)*unit

    if r > 100 and r % 10 > 0:
        r = (r/10)*10

    if r == 0:
        r = unit

    quantity = r
    if activity_dict['price'] == 0:
        quantity = 1
    return account['user_id'], account['token'], quantity


def choose_activity(activitys): 
    weight = 100000
    count = len(activitys)
    diff = weight/count
    for a in activitys:
        left_amount = a['target_amount'] - a['current_amount']
        a['weight'] = weight + left_amount * 0.5
        if a['price'] == 0:
            a['weight'] += 20000
        if a['unit'] > 1:
            update_weight = a['weight'] - 200 * a['unit']
            a['weight'] = update_weight if update_weight > 0 else 1000
        weight -= diff
        if weight <= 0:
            weight = 1000
    candidates = [x for x in weight_sample(activitys, 1)]
    return candidates[0]


def monitor_activity(diaosi=False):
    while True:
        now = local_now()
        time.sleep(25)
        activitys = get_available_activitys(diaosi)
        if not activitys:
            continue
        activity = choose_activity(activitys)
        # check if virtual account in
        has_in, size = has_virtual_account_in(activity['id'])
        if need_virtual_buy(activity['id']):
            user_id, token, quantity = select_buy_info_latest(activity, diaosi)
            res = buy(user_id, token, activity['id'], quantity)
            if res:
                data = json.loads(res).get('data')
                if data:
                    print activity['target_amount']
                    pass
            else:
                print res
        else:
            print 'no need to involve virtual has_in:%s' % has_in
        if diaosi:
            rand_ts = random.randint(1, 10)
        else:
            rand_ts = random.randint(20, 40)
        time.sleep(rand_ts)


def get_available_activitys(diaosi):
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
    print 'choose rand:%s' % choose_rand
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
        print r.text
        if r.status_code == 200:
            return r.text
        else:
            print r.text
            return None
    except Exception as e:
        print 'buy requests exceptions, %s' % e
        return None


def buy_one(activity_id, quantity=1):
    account = random.choice(account_list)
    res = buy(account['user_id'], account['token'], activity_id, quantity)
    return res


if __name__ == "__main__":
    load_account_from_db()
    if len(sys.argv) > 1 and sys.argv[1] == 'diaosi':
        monitor_activity(diaosi=True)
    if len(sys.argv) > 1 and sys.argv[1] == 'one':
        activity_id = sys.argv[2]
        quantity = int(sys.argv[3])
        buy_one(activity_id, quantity=quantity)
    else:
        monitor_activity()
