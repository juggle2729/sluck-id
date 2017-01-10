# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import redis
from pymongo import MongoClient


db = MongoClient('10.168.5.23').lucky
redis_db = redis.StrictRedis(host='10.46.71.31', port=19000) 
items = db.user_stats.find()
count = 0
for item in items:
    user_id = item['_id']
    if item.get('pay'):
        total_pay = item['pay'].get('total') or 0
        redis_db.hset('stats:user:%s' % user_id, 'total_pay', total_pay)
        count += 1

print 'set %d user' % count
