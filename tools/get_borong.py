# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import datetime


# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.utils.tz import local_to_utc


from luckycommon.model.activity import ActivityWin, UserActivity, Activity
from luckycommon.model.pay import Pay


start_time = '2017-03-01 00:00:01'
end_time = '2017-03-09 23:59:59'

start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')



activity_win_query = ActivityWin.query.filter(
    ActivityWin.updated_at  >=  start_time.strftime('%Y-%m-%d %H:%M:%S')).filter(
    ActivityWin.updated_at  <=  end_time.strftime('%Y-%m-%d %H:%M:%S')).order_by(
    ActivityWin.updated_at.desc()).all()

users = set()

print 'time, order ID, UID, activity name, amount'
for item in activity_win_query:
    user_id = item.winner
    activity_id = item.activity_id
    order_id = item.order_id
    user_activity = UserActivity.query.filter(UserActivity.user_id == user_id).filter(UserActivity.activity_id == activity_id).first()
    user_numbers = user_activity.numbers.split(',')
    activity = Activity.query.filter(Activity.id == activity_id).first()
    if not activity:
        continue
    if len(user_numbers) == activity.target_amount:
        # print '%s user: %s, buy all in activity: <%s, %s>' % (user_activity.updated_at, user_id, activity.template_id, activity_id)
        print  '%s, %s, %s, %s, %s,' % (user_activity.updated_at, order_id, user_id, activity.name, activity.target_amount)
        users.add(user_id)


print 'user ID, charge num, charge amount, win num, win amount,'
for user_id in users:
    # 获取充值信息
    pays = Pay.query.filter(Pay.user_id == user_id).filter(Pay.status == 2).filter(
    Pay.updated_at >= start_time.strftime('%Y-%m-%d %H:%M:%S')).filter(
    Pay.updated_at <= end_time.strftime('%Y-%m-%d %H:%M:%S')).all()
    charge_num = len(pays)
    amount = 0
    for pay in pays:
        if pay.price is not None:
            amount += pay.price
    # 获取中奖信息
    wins = ActivityWin.query.filter(
    ActivityWin.updated_at  >=  start_time.strftime('%Y-%m-%d %H:%M:%S')).filter(
    ActivityWin.updated_at  <=  end_time.strftime('%Y-%m-%d %H:%M:%S')).filter(
    ActivityWin.winner == user_id).all()
    win_num = len(wins)
    win_amount = 0
    for activity_win in wins:
        activity = Activity.query.filter(Activity.id == activity_win.activity_id).first()
        if not activity:
            continue
        win_amount = win_amount + (activity.target_amount * activity.price)

    print '%s, %s, %s, %s, %s,' % (user_id, charge_num, amount, win_num, win_amount)