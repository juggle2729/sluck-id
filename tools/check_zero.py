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

from luckycommon.model import orm
from luckycommon.model.activity import UserActivity, Activity, ActivityWin
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
    items = Activity.query.filter(Activity.template_id == 208).all()
    a_list = []
    for item in items:
        a_list.append(item.id)
    win_items = orm.session.query(ActivityWin.winner).filter(ActivityWin.activity_id.in_(a_list)).all()
    uids = set()
    for winner in win_items:
        uids.add(winner[0])
    for uid in uids:
        if redis_cache.is_virtual_account(uid):
            continue
        stats = redis_cache.get_user_stats(uid) 
        print '%s\t%s\t%s\t%s' % (uid, stats.get('total_recharge', 0), stats.get('win_count', 0), stats.get('total_win', 0))
