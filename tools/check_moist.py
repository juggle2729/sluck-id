# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.campaign.moist_campaign import handler

from luckycommon.cache import redis_cache
from luckycommon.model.pay import Pay
from luckycommon.utils.tz import utc_to_local


cmd = sys.argv[1]
if cmd == 'check':
    pay_list = Pay.query.filter(Pay.created_at > '2016-03-14 02:05:00').filter(Pay.status == 2).filter(Pay.price >= 50).all()
    count = 0
    for pay in pay_list:
        user_id = pay.user_id
        price = pay.price
        handler.add_new_recharge(user_id, price)
        print 'add new moist, user_id:%s, price:%s' % (user_id, price)
        count += 1
    print 'count:%s' % (count)
