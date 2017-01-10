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

from luckycommon.campaign import recharge_campaign
from luckycommon.cache import redis_cache
from luckycommon.account.model.account import Account
from luckycommon.model.pay import Pay
from luckycommon.model.activity import ActivityWin
from luckycommon.model.transaction import Transaction
from luckycommon.db.activity import get_activity
from luckycommon.utils.tz import utc_to_local
from luckycommon.utils.mail import MailSender


EXPORT_PATH = '/home/ubuntu/af-env/data/stats/'
mail_sender = MailSender.getInstance()
mail_sender.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@adsquare-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@adsquare-tech.com>',
    'to': ['wangshanshan@adsquare-tech.com',
           'wangfeng@adsquare-tech.com',
           'jiangyan@adsquare-tech.com',
           'jack@adsquare-tech.com',
           'shuxiang@adsquare-tech.com']
    #'to': ['shuxiang@adsquare-tech.com']
})


def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path


cmd = sys.argv[1]
if cmd == 'check':
    items = Account.query.filter(Account.created_at > '2016-06-01 16:00:00').all()
    u_list = []
    for item in items:
        uid = item.id
        if redis_cache.is_virtual_account(uid):
            continue
        user_stats = redis_cache.get_user_stats(uid)
        total_recharge = user_stats.get('total_recharge', 0)
        created_at = item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        first_pay = Pay.query.filter(Pay.user_id == uid).filter(Pay.status == 2).first()
        if first_pay:
            first_pay_amount = first_pay.price
            first_pay_at = first_pay.created_at.strftime('%Y-%m-%d %H:%M:%S')
        else:
            first_pay_amount = 0
            first_pay_at = 0
        u_list.append((uid, first_pay_amount, first_pay_at, created_at, total_recharge))
    u_list.sort(key=lambda x:x[4], reverse=True)
    for u in u_list:
        print '%s\t%s\t%s\t%s\t%s' % (u[0], u[1], u[2], u[3], u[4])


if cmd == 'check':
    pay_list = Pay.query.filter(Pay.status == 2).filter(Pay.created_at > '2016-05-03 16:00:00').filter(Pay.created_at < '2016-05-04 01:50:00').all()
    count = 0
    for pay in pay_list:
        user_id = pay.user_id
        price = pay.price
        recharge_campaign.add_new_recharge(user_id, price)
        print 'add new recharge %s to %s' % (price, user_id)
        count += 1
    print 'totaly add %d count' % count

if cmd == 'win':
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=1)
    start_date = start_date.replace(hour=16, minute=0, second=0, microsecond=0)
    win_list = ActivityWin.query.filter(ActivityWin.created_at > start_date.strftime('%Y-%m-%d %H:%M:%S')).all()
    print len(win_list)
    rank_list = []
    for win in win_list:
        winner = win.winner
        activity_id = win.activity_id
        activity = get_activity(activity_id)
        if redis_cache.is_virtual_account(winner):
            continue
        rank_list.append({'activity': activity.name, 'winner': winner, 'amount': activity.target_amount, 'time': utc_to_local(win.created_at)})
    rank_list.sort(key=lambda x: x.get('amount'), reverse=True)
    user_list = []
    for item in rank_list:
        print '%s\t%s\t%s\t%s' % (item['activity'], item['winner'], item['amount'], item['time'].strftime('%Y-%m-%d %H:%M:%S'))
        user_list.append((item['activity'], item['winner'], item['amount'], item['time']))
    print 'rank size %s' % len(rank_list)
    excel_header = [u'商品名称', u'中奖者id', u'活动价格', u'中奖时间']
    file_path = redirect_to_file(user_list, excel_header, u'win_data.xlsx')
    mail_sender.send(u"今日渠道用户中奖排名", u'详情请见附件', attachments=[file_path])

if cmd == 'transaction':
    user_id = sys.argv[2]
    items = Transaction.query.filter(Transaction.user_id == user_id).order_by(Transaction.created_at).all()
    t_list = []
    for item in items:
        t = item.type
        if t == 1:
            t = u'充值' 
        if t == 2:
            t = u'系统奖励' 
        if t == 4:
            t = u'余额购买' 
        print '%s\t%s\t%s\t%s\t%s\t%s' % (item.id, t, item.title, item.price, item.balance, item.order_id)
