# -*- coding: utf-8 -*-
#from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.order.handler import show_order

from luckycommon.cache import redis_cache
from luckycommon.order.model.order import AwardedOrder, ORDER_STATUS
from luckycommon.order.db.order import receipt_order
from luckycommon.utils import id_generator



if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        order_list = AwardedOrder.query.filter(AwardedOrder.status == ORDER_STATUS.DEAL).all()
        for order in order_list:
            try:
                show_order(order)
            except Exception as e:
                print 'show order exception, %s' % e
        print 'changed %d status' % len(order_list)
    elif cmd == 'receipt':
        fd = open('/home/ubuntu/af-env/luckyservice/tools/virtual_list', 'r')
        count = 0
        for line in fd:
            line = line.strip()
            gid, term_number, uid = line.split('\t')
            if not redis_cache.is_virtual_account(int(uid)):
                print '%s is not virtual account' % uid
                continue
            activity_id = id_generator.generate_uuid(
                'activity:%s:%s' % (gid, term_number))
            order = Order.query.filter(Order.activity_id == activity_id).filter(Order.status == 4).first()
            if order.buyer != int(uid):
                print 'buyer error, %s %s' % (order.buyer, uid)
                continue
            receipt_order(order.id)
            show_order(order)
            count += 1
        print 'fix %d order' % count
