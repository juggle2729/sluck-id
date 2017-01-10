# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import logging
from datetime import timedelta


# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.db.account import get_account
from luckycommon.stats import MG as mg
from luckycommon.db.missed_vips import batch_insert_active_top
from luckycommon.model import orm
from luckycommon.db import account as account_db
from luckycommon.utils.tz import local_now, get_utc_date

_LOGGER = logging.getLogger(__name__)


def dump_users(start_time, end_time, d_type):
    stats = mg.daily_stats.aggregate([
        {'$match': {'updated_at': {'$gte': start_time, '$lt': end_time}}},
        {'$group': {'_id': '$user_id',
                    'recharge_amount': {'$sum': '$recharge.total'},
                    'win_amount': {'$sum': '$win.total'},
                    'win_count': {'$sum': '$win.count'}}},
        {'$sort': {'recharge_amount': -1}},
        {'$limit': 100}
    ])
    to_insert = []
    for stat in stats:
        data = {
            'uid': stat['_id'],
            'recharge_amount': stat['recharge_amount'],
            'win_count': stat['win_count'],
            'win_amount': stat['win_amount'],
            'type': d_type
        }
        to_insert.append(data)

    return to_insert


def main(period):
    today = get_utc_date()
    if period == 'week':
        start_time = today - timedelta(days=7)
        d_type = 0
    elif period == '15days':
        start_time = today - timedelta(days=15)
        d_type = 1
    elif period == 'month':
        yesterday = today - timedelta(days=1)
        start_time = get_utc_date((today - timedelta(
            days=yesterday.day - 1)).strftime('%Y-%m-%d'))
        d_type = 2
    else:
        assert False
    to_insert = dump_users(start_time, today, d_type)
    batch_insert_active_top(to_insert)

if __name__ == '__main__':
    main(sys.argv[1])
