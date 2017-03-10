# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import logging
from datetime import datetime, timedelta


# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.db.account import get_account
from luckycommon.account.model.account import Account
from luckycommon.stats import MG as mg
from luckycommon.db.missed_vips import batch_insert_missed_vips
from luckycommon.model.missed_vips import MissedVips
from luckycommon.model import orm
from luckycommon.db import account as account_db
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)

missed_users = {
    1: set(),
    2: set(),
    3: set()
}
for k in (1, 2, 3):
    items = orm.session.query(MissedVips.uid).filter(
        MissedVips.type == k).all()
    for item in items:
        missed_users[k].add(item[0])

missed_users[1] -= missed_users[2]
missed_users[2] -= missed_users[3]

all_missed = missed_users[1] | missed_users[2] | missed_users[3]


def dump_vip_users(lost_days=3, missed_times=0):
    now = datetime.now()
    start_date = now - timedelta(days=lost_days)
    start_date = start_date.replace(hour=16, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)

    filters = {'updated_at': {'$lte': end_date, '$gte': start_date},
               'recharge.total': {'$gt': 100}}

    if missed_times == 0:
        filters['_id'] = {'$nin': list(all_missed)}
    else:
        filters['_id'] = {'$in': list(missed_users[missed_times])}

    user_stats = mg.user_stats.find(filters).sort(
        'recharge.total', -1).limit(100)
    return user_stats


def dump_new_users():
    now = datetime.now()
    updated_at_upper = now - timedelta(days=3)
    created_at_lower = now - timedelta(days=10)
    created_at_lower = created_at_lower.replace(
        hour=16, minute=0, second=0, microsecond=0)
    created_at_upper = created_at_lower + timedelta(days=1)
    filters = {
        'created_at': {'$gte': created_at_lower, '$lt': created_at_upper},
        'recharge.total': {'$gt': 0, '$lte': 100},
        'updated_at': {'$lt': updated_at_upper}}
    user_stats = mg.user_stats.find(filters).sort(
        'recharge.total', -1)
    insert_list = []
    forbidden_users = orm.session.query(Account.id).filter(
        Account.status != 0).all()
    forbidden_users = [x[0] for x in forbidden_users]
    forbidden_users = set(forbidden_users)
    for user_stat in user_stats:
        if user_stat['_id'] not in forbidden_users:
            insert_list.append(user_stat)
    return insert_list


def get_insert_list(user_stats, lost_days, type, user_type=0):
    insert_list = []
    for user_stat in user_stats:
        user_id = int(user_stat['_id'])
        register_chn = user_stat.get('chn') or u'未知'
        created_at = user_stat.get('created_at')
        if not created_at:
            created_at = get_account(user_id).created_at
        created_at = utc_to_local_str(created_at)
        updated_at = utc_to_local_str(user_stat['updated_at'])
        recharge_amount = int(user_stat['recharge']['total'])
        pay_count = user_stat.get('pay', {}).get('count', 0)
        if 'win' in user_stat:
            win_count = user_stat['win']['count']
            win_amount = user_stat['win']['total']
        else:
            win_count = 0
            win_amount = 0
        active_count = mg.daily_stats.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "count": {"$sum": 1}}}
        ])
        active_days = active_count.next().get(
            'count', 0) if active_count.alive else 0
        account = account_db.get_account(user_id)
        user_info = {
            'uid': user_id,
            'nick_name': account.nick_name,
            'phone': account.phone[2:],
            'chn': register_chn,
            'type': type,
            'user_type': user_type,
            'created_time': created_at,
            'active_days': active_days,
            'updated_time': updated_at,
            'lost_days': lost_days,
            'recharge_amount': recharge_amount,
            'pay_count': pay_count,
            'win_count': win_count,
            'win_amount': win_amount
        }
        insert_list.append(user_info)
    return insert_list


try:
    for k in (3, 7, 14):
        user_stats = dump_vip_users(k, 0)
        insert_list = get_insert_list(user_stats, k, 1)
        batch_insert_missed_vips(insert_list)
    user_stats = dump_vip_users(7, 1)
    insert_list = get_insert_list(user_stats, 7, 2)
    batch_insert_missed_vips(insert_list)
    user_stats = dump_vip_users(30, 2)
    insert_list = get_insert_list(user_stats, 30, 3)
    batch_insert_missed_vips(insert_list)

    user_stats = dump_new_users()
    insert_list = get_insert_list(user_stats, 3, 1, 1)
    batch_insert_missed_vips(insert_list)
except Exception as e:
    _LOGGER.exception(e)
