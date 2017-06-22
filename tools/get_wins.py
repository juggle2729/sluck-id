# -*- coding: utf-8 -*-
from __future__ import absolute_import

import datetime
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.activity import ActivityWin, UserActivity, Activity
from luckycommon.cache import redis_cache
from luckycommon.account.db.account import get_account_status
from luckycommon.utils.mail import TOOL_MAIL_SENDER


def get_today_activity_win(start_time, end_time):
    activity_win_query = ActivityWin.query.filter(
        ActivityWin.updated_at >= start_time.strftime('%Y-%m-%d %H:%M:%S')).filter(
        ActivityWin.updated_at <= end_time.strftime('%Y-%m-%d %H:%M:%S')).order_by(
        ActivityWin.updated_at.desc()).all()
    return activity_win_query


if __name__ == '__main__':
    today = datetime.datetime.utcnow()
    yesterday = today + datetime.timedelta(days=-1)
    before_yesterday = yesterday + datetime.timedelta(days=-1)
    start_time = '%s 17:00:00' % before_yesterday.strftime('%Y-%m-%d')
    end_time = '%s 16:59:59' % yesterday.strftime('%Y-%m-%d')
    start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    activity_wins = get_today_activity_win(start_time, end_time)
    NORMAL_AMOUNT = 0
    BORONG_AMOUNT = 0
    BORONG_NUM_DIC = {}

    html_str = u'<html><head></head><body><h2> 每日中奖信息（%s）</h2>' % yesterday.strftime('%Y-%m-%d')
    table_1 = u'<table border="1"><tr><th>Activity ID</th><th>Activity Name</th><th>Amount</th>' \
              u'<th>Winner</th><th>Order ID</th></tr>'
    table_2 = u'<table border="1"><tr><th>Activity ID</th><th>Activity Name</th><th>Amount</th>' \
              u'<th>Winner</th><th>Order ID</th></tr>'
    table_3 = u'<table border="1"><tr><th>Activity Name</th><th>Borong count</th></tr>'

    for item in activity_wins:
        activity_id = item.activity_id
        user_id = item.winner
        if redis_cache.is_virtual_account(user_id):  # virtual account
            continue
        if get_account_status(user_id):  # black list account
            continue
        order_id = item.order_id
        user_activity = UserActivity.query.filter(UserActivity.user_id == user_id).filter(
            UserActivity.activity_id == activity_id).first()
        user_numbers = user_activity.numbers.split(',')
        activity = Activity.query.filter(Activity.id == activity_id).first()
        if not activity:
            continue
        if len(user_numbers) == activity.target_amount:  # 包场购买
            BORONG_AMOUNT += activity.price * activity.target_amount
            table_2 += u'<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                activity.id, activity.name, activity.price * activity.target_amount, user_id, order_id)
        else:
            NORMAL_AMOUNT += activity.price * activity.target_amount
            table_1 += u'<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                activity.id, activity.name, activity.price * activity.target_amount, user_id, order_id)
            if BORONG_NUM_DIC.get(activity.name) is None:
                BORONG_NUM_DIC[activity.name] = 1
            else:
                BORONG_NUM_DIC[activity.name] += 1

    for k, v in BORONG_NUM_DIC.items():
        table_3 += u'<tr><td>%s</td><td>%s</td></tr>' % (k, v)
    table_3 += u'</table>'
    table_1 += u'</table>'
    table_2 += u'</table>'
    html_str += u'<h3>真实用户中奖金额: %s, 包场用户中奖金额: %s.</h3>' % (str(NORMAL_AMOUNT), str(BORONG_AMOUNT))
    html_str += u'<h3>包场用户中奖商品的统计:</h3>'
    html_str += table_3
    html_str += u'<h3>真实用户中奖:</h3>'
    html_str += table_1
    html_str += u'<h3>包场用户中奖:</h3>'
    html_str += table_2
    html_str += u'</body></html>'
    TOOL_MAIL_SENDER.send(u"%s -- 每日中奖信息 " % yesterday.strftime('%Y-%m-%d'), html_str)
