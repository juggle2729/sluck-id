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

from luckycommon.model.activity import UserActivity
from luckycommon.db.account import get_account
from luckycommon.cache import redis_cache
from luckycommon.model.pay import Pay
from luckycommon.utils.tz import utc_to_local
from luckycommon.utils.mail import MailSender


EXPORT_PATH = '/home/ubuntu/af-env/data/stats/'
mail_sender = MailSender.getInstance()
mail_sender.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@adsquare-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@adsquare-tech.com>',
    'to': [
        'wangshanshan@adsquare-tech.com',
        'wangfeng@adsquare-tech.com',
        'jack@adsquare-tech.com',
        'jiangyan@adsquare-tech.com',
        'shuxiang@adsquare-tech.com']
    #'to': ['shuxiang@adsquare-tech.com']
})


BMW_ID = 'b14e6a38-d0bf-303e-9e5f-0394cea487e5'


def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path


cmd = sys.argv[1]
if cmd == 'check':
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=1)
    start_date = start_date.replace(hour=16, minute=0, second=0, microsecond=0)
    pay_list = Pay.query.filter(Pay.status == 2).filter(Pay.created_at > start_date.strftime('%Y-%m-%d %H:%M:%S')).all()
    user_set = set()
    user_bmw_set = set()
    old_user_set = set()
    old_user_bmw_set = set()
    new_user_set = set()
    new_user_bmw_set = set()
    for pay in pay_list:
        user_id = pay.user_id
        item = UserActivity.query.filter(UserActivity.user_id == user_id).filter(UserActivity.activity_id == BMW_ID).first()
        account = get_account(user_id)
        is_fresh = True if account.created_at > start_date else False
        if item:
            user_bmw_set.add(user_id)
            if is_fresh:
                new_user_bmw_set.add(user_id)
            else:
                old_user_bmw_set.add(user_id)
        user_set.add(user_id)
        if is_fresh:
            new_user_set.add(user_id) 
        else:
            old_user_set.add(user_id) 
    print 'total', len(user_set), len(user_bmw_set)
    print 'new', len(new_user_set), len(new_user_bmw_set)
    print 'old', len(old_user_set), len(old_user_bmw_set)
    
    items = UserActivity.query.filter(UserActivity.activity_id == BMW_ID).all()
    print '%d person buy bmw' % len(items)
    record_list = []
    for item in items:
        nums = item.numbers.split(',')
        record_list.append({
            'uid': item.user_id,
            'count': len(nums)
        })
    record_list.sort(key=lambda x: x.get('count'), reverse=True)
    print record_list[:10]

if cmd == 'start':
    items = UserActivity.query.filter(UserActivity.activity_id == BMW_ID).all()
    buy_list = []
    for item in items:
        user_id = item.user_id
        numbers = item.numbers.split(',')
        num_count = len(numbers)
        user_stats = redis_cache.get_user_stats(user_id) 
        total_recharge = int(user_stats.get('total_recharge', 0))
        total_win = int(user_stats.get('total_win', 0))
        buy_list.append((
            user_id,
            num_count,
            total_recharge,
            total_win
        ))
    excel_header = [u'用户ID', u'购买次数', u'充值额度', u'中奖额度']
    file_path = redirect_to_file(
        buy_list, excel_header, u'daily_bmw.xlsx')
    mail_sender.send(u"宝马用户日报", '详情请见附件', attachments=[file_path])
