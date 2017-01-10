# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import tablib
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckyapi.logic.crowdfunding import create_activity_lite

from luckycommon.cache import redis_cache
from luckycommon.order.model.order import *
from luckycommon.order.db import order as order_db


cmd = sys.argv[1]
if cmd == 'start':
    aid = sys.argv[2]
    orders, count = order_db.get_activity_orders(aid)
    count = 0
    for order in orders:
        order_id = order.id
        order_number = OrderNumber.query.filter(OrderNumber.order_id == order_id).first()
        if order_number:
            continue
        numbers = order.lucky_numbers 
        Order.query.filter(Order.id == order_id).update({
            'lucky_numbers': None
        }) 
        order_number = OrderNumber()
        order_number.order_id = order_id
        order_number.numbers = numbers
        order_number.save()
        print 'detached order %s' % order_id
        count += 1
    print 'detached %s count' % count
