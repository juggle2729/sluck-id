# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.account.db.account import is_virtual_user
from luckycommon.model.activity import ActivityWin, Activity
from luckycommon.order.model.order import Order

real_winner_list = []
virtual_winner_list = []
total_win = 0
total_buy = 0
real_win = 0
real_buy = 0
virtual_win = 0
virtual_buy = 0

for win in ActivityWin.query.filter(ActivityWin.updated_at > '2017-04-06 11:00:00').all():
    winner = win.winner
    activity = Activity.query.filter(Activity.id == win.activity_id).first()
    total_win += activity.target_amount
    if is_virtual_user(winner):
        virtual_win += activity.target_amount
        virtual_winner_list.append(winner)
    else:
        real_win += activity.target_amount
        real_winner_list.append(winner)

for order in Order.query.filter(Order.updated_at > '2017-04-06 11:00:00').filter(Order.status == 2).all():
    user_id = order.buyer
    total_buy += order.total_price
    if is_virtual_user(user_id):
        virtual_buy += order.total_price
    else:
        real_buy += order.total_price

for order in Order.query.filter(Order.updated_at > '2017-04-06 11:00:00').filter(Order.status == 4).all():
    user_id = order.buyer
    total_buy += order.total_price
    if is_virtual_user(user_id):
        virtual_buy += order.total_price
    else:
        real_buy += order.total_price

print 'total_win: %s, total_buy: %s, real_win: %s, virtual_win: %s, real_buy: %s, virtual_buy: %s, real_winner_count: %s, virtual_winner_count: %s' % (
    total_win, total_buy, real_win, virtual_win, real_buy, virtual_buy, len(real_winner_list), len(virtual_winner_list))
