# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.model import orm
from luckycommon.order.model.order import Order, ORDER_STATUS
from luckycommon.model.transaction import Transaction, TRANSACTION_TYPE



if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        order_list = Order.query.filter(Order.created_at > '2016-04-10 16:00:00').all()
        v_set = set()
        h_set = set()
        real_count = 0
        virtual_count = 0
        real_money = 0
        virtual_money = 0
        for order in order_list:
            if redis_cache.is_virtual_account(order.buyer):
                v_set.add(order.buyer)
                virtual_count += 1
                virtual_money += order.goods_quantity
            else:
                h_set.add(order.buyer)
                real_count += 1
                real_money += order.goods_quantity
        print 'count, real:%s  virtual:%s' % (real_count, virtual_count)
        print 'money, real:%s  virtual:%s' % (real_money, virtual_money)
        print 'v user count:%s, h user count:%s' % (len(v_set), len(h_set))
    if cmd == 'transaction':
        vids = redis_cache.get_virtual_account()
        v_list = []
        for vid in vids:
            items = orm.session.query(Transaction.price).filter(Transaction.user_id == vid)\
                                     .filter(Transaction.type == TRANSACTION_TYPE.BALANCE_BUY).all()
            consume = 0
            for item in items:
                price = item[0]
                consume += price
            v_list.append({'vid': vid, 'consume': consume})
        v_list.sort(key=lambda x:x.get('consume'), reverse=True)
        fp = open('./top_agent', 'w')
        for v in v_list:
            fp.write('%s\t%s\n' % (v['vid'], v['consume']))
        fp.close()
