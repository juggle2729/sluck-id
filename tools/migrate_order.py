# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.order.model.order import Order, AwardedOrder, ORDER_STATUS
from luckycommon.order.db.order import receipt_order
from luckycommon.db.activity import get_activity
from luckycommon.utils import id_generator



if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        order_list = Order.query.filter(Order.status >= ORDER_STATUS.AWARDED).all()
        count = 0
        for order in order_list:
            try:
                user_id = order.buyer
                activity_id = order.activity_id
                if redis_cache.is_virtual_account(user_id):
                    continue
                activity = get_activity(activity_id)
                awarded_order = AwardedOrder()
                awarded_order.order_id = order.id
                awarded_order.user_id = order.buyer
                awarded_order.activity_id = activity.id
                awarded_order.activity_name = activity.name
                awarded_order.term_number = activity.term_number
                awarded_order.status = order.status
                awarded_order.receipt_address = order.receipt_address
                awarded_order.extend = order.extend
                extend_obj = {} if not order.extend else json.loads(order.extend) or {}
                if 'remark' in extend_obj:
                    awarded_order.remark = extend_obj['remark']
                awarded_order.created_at = order.created_at
                awarded_order.updated_at = order.updated_at
                awarded_order.save()
                count += 1
            except Exception as e:
                print 'migrate order exception, %s' % e
        print 'migrated %d order' % count
