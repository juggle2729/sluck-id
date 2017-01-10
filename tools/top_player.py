# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
from datetime import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.model.pay import Pay
from luckycommon.account.model.account import Account
from luckycommon.db.activity import get_activity
from pymongo import MongoClient


db = MongoClient('10.168.5.23').lucky


user_dict = {}
super_list = []
strong_list = []
common_list = []

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        items = Pay.query.filter(Pay.status == 2).all()
        for item in items:
            user_id = item.user_id
            user_dict.setdefault(user_id, {'count':0,'price':0})
            info = user_dict[user_id]
            info['count'] += 1
            info['price'] += item.price

        user_list = [{'uid':k,'count':v['count'],'price':v['price']} for k,v in user_dict.items()]
        user_list.sort(key=lambda x:x.get('price'), reverse=True)
        for user in user_list:
            if user['price'] > 1000:
                super_list.append(user)
                print '%s\t%s\t%s' % (user['uid'], user['count'], user['price'])
            elif user['price'] > 100:
                strong_list.append(user)
            elif user['price'] > 10:
                common_list.append(user)
        print 'total:%s, super:%s, strong:%s, common:%s' % (len(user_list), len(super_list), len(strong_list), len(common_list))
    elif cmd == 'user':
        user_list = []
        users = Account.query.all()
        for user in users:
            if redis_cache.is_virtual_account(user.id):
                continue
            user_stats = db.user_stats.find_one({'_id': user.id}) or {}
            recharge_stats = user_stats.get('recharge', {})
            pay_stats = user_stats.get('pay', {})
            win_stats = user_stats.get('win', {})
            total_recharge = recharge_stats.get('total', 0)
            total_pay = pay_stats.get('total', 0)
            total_win = win_stats.get('total', 0)
            if not user_stats or not user_stats.get('updated_at') or not user_stats.get('created_at'):
                last_active = datetime.strftime(user.created_at, '%Y-%m-%d %H:%M:%S')
                create_time = datetime.strftime(user.created_at, '%Y-%m-%d %H:%M:%S')
            else:
                last_active = datetime.strftime(user_stats.get('updated_at'), '%Y-%m-%d %H:%M:%S')
                create_time = datetime.strftime(user_stats.get('created_at'), '%Y-%m-%d %H:%M:%S')
            data = {'uid': user.id, 'recharge': total_recharge, 'pay': total_pay, 'win': total_win, 'created_at': create_time, 'last_active': last_active}
            user_list.append(data)
            print data
        user_list.sort(key=lambda x:x.get('recharge'), reverse=True)
        fp = open('./top_player', 'w')
        for user in user_list:
            fp.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (user['uid'], user['recharge'], user['pay'], user['win'], user['created_at'], user['last_active']))
        fp.close()
