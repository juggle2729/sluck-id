# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.activity import Activity, ActivityWin
from luckycommon.order.model.order import Order
from luckycommon.account.db.account import is_virtual_user

updated_at = '2017-04-06 13:20:00'
activities = Activity.query.filter(Activity.created_at >= updated_at).filter(Activity.status == 4).all()
total_price = 0
virtual_users = []
virtual_buy = 0
real_users = []
real_buy = 0
real_wins = 0
virtual_wins = 0
for activity in activities:
    activity_win = ActivityWin.query.filter(ActivityWin.activity_id == activity.id).first()
    orders = Order.query.filter(Order.activity_id == activity.id).all()
    is_virtual = is_virtual_user(activity_win.winner)
    order_num = 0
    if is_virtual:
        virtual_users.append(activity_win.winner)
        virtual_wins += activity.target_amount
    else:
        real_users.append(activity_win.winner)
        real_wins += activity.target_amount
    for order in orders:
        is_virtual = is_virtual_user(order.buyer)
        if is_virtual:
            virtual_buy += order.goods_quantity
            order_num += order.goods_quantity
        else:
            real_buy += order.goods_quantity
            order_num += order.goods_quantity
    total_price += activity.target_amount
    if order_num != activity.target_amount:
        print 'error --------- %s' % activity.id
print 'total_price, virtual_buy, virtual_wins, real_buy, real_wins: %s,%s,%s,%s,%s' \
        % (total_price, virtual_buy, virtual_wins, real_buy, real_wins)
