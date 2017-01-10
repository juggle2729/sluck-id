# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from pymongo import MongoClient
from luckycommon.cache import redis_cache
from luckycommon.model.account import AccountThird
from luckycommon.utils.tz import utc_to_local

db = MongoClient('10.168.5.23').lucky


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        dd = sys.argv[2]
        now = datetime.datetime.strptime(dd, '%Y-%m-%d')
        #now = utc_to_local(datetime.datetime.now())
        start_date = now - datetime.timedelta(days=3)
        start_date = start_date.replace(hour=0)
        end_date = now - datetime.timedelta(days=2)
        end_date = end_date.replace(hour=0)
        print start_date, end_date
        items = db.user_stats.find({'$and': [{'created_at':{'$gte': start_date}},{'created_at':{'$lte': end_date}}]})
        bingo_list = []
        count = 0
        for item in items:
            if not item.get('first_login_at'):
                continue
            user_id = item['_id']
            account_third = AccountThird.query.filter(AccountThird.user_id == user_id).first()
            if account_third:
                continue
            count += 1
            created_at = item['created_at']
            updated_at = item['updated_at']
            if created_at.day != updated_at.day:
                print created_at, updated_at
                bingo_list.append(user_id)
        print 'total_count:%s, active_count:%s' % (count, len(bingo_list))
