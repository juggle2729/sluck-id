# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import random
import logging
from datetime import timedelta

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.push import handler as push_handler

from luckycommon.credit.model.credit import *
from luckycommon.credit.db import credit as credit_db
from luckycommon.account.db.account import get_account
from luckycommon.utils.tz import local_now

from future.utils import raise_with_traceback

_LOGGER = logging.getLogger('worker')


def is_loser(user_id, target_amount):
    user_stats = redis_cache.get_user_stats(user_id)
    if not user_stats:
        return False
    total_recharge = int(user_stats.get('total_recharge', 0))
    total_win = int(user_stats.get('total_win', 0))
    last_win = int(user_stats.get('last_win', 0))
    if total_recharge < 20 or float(total_recharge - total_win - target_amount)/total_recharge < -0.1:
        return False
    exist_record = DistributeRecord.query.filter(DistributeRecord.user_id == user_id).first()
    if exist_record:
        rand = random.randint(1, 100)
        if rand < 80:
            return False
    return True


def start():
    end_date = local_now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(1)

    pool_amount = redis_cache.get_credit_pool() or 0
    # create term record
    distribute_term = DistributeTerm()
    distribute_term.date = start_date.strftime('%Y-%m-%d')
    distribute_term.pool_amount = pool_amount
    distribute_term.save()
    redis_cache.clear_credit_pool()

    divided_amount = int(pool_amount) / 100
    _LOGGER.info('start distribute credit pool, total amount:%s, divided credit:%s', pool_amount, divided_amount)
    target_users = set()
    account_signs = credit_db.get_sign_users(start_date, end_date)
    for account_sign in account_signs:
        user_id = account_sign.user_id
        is_valid = is_loser(user_id, divided_amount/1000)
        if is_valid:
            target_users.add(user_id)
    supply_count = 100 - len(target_users)
    if len(target_users) < 100:
        while True:
            agent_id = redis_cache.get_random_virtual_account()
            target_users.add(int(agent_id))
            if len(target_users) >= 100:
                break
    target_users = random.sample(target_users, 100)
    # create detail record
    term_id = distribute_term.id
    for user_id in target_users:
        credit_db.add_credit(user_id, divided_amount, u'幸运元宝')
        account = get_account(user_id)
        user_info = {
            'nick_name': account.nick_name, 
            'avatar_id': account.avatar_id,
        }
        record = DistributeRecord()
        record.term_id = term_id
        record.user_id = user_id
        record.user_info = json.dumps(user_info, ensure_ascii=False)
        record.amount = divided_amount
        record.save()
        push_handler.push_sign_award(user_id, divided_amount)
    _LOGGER.info('distributed credit pool, total amount:%s, divided credit:%s, supply count:%s',
        pool_amount, divided_amount, supply_count)
    

if __name__ == "__main__":
    start()
