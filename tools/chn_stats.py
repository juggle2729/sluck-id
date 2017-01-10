# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
from datetime import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.model.pay import Pay
from luckycommon.model.account import Account
from luckycommon.db.activity import get_activity
from pymongo import MongoClient


db = MongoClient('10.168.5.23').lucky


chn_dict = {}
"""
chn_dict = {
    'lic01': {
            '2016-01': {
                'total_count': 100,  # 总人数
                'total_life_day': 100,  # 总生命周期
                'total_recharge_amount': 10000,  # 总充值金额
                'total_recharge_count': 100,     # 总充值次数
                'monthly_recharge': {  # 每月充值(次数，金额)
                    '2016-01': (100, 10000),
                    '2016-02': (200, 20000)
                }
            }
    } 
}
"""

CHN_LIST = ['lic01','yingyongbao','lic04','huawei','jiangy05','ios','oppo']
chn_dict = {'lic01': {}, 'yingyongbao': {}, 'lic04': {}, 'huawei': {}, 'jiangy05': {}, 'ios': {}, 'oppo': {}}


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'user':
        users = db.user_stats.find({'created_at': {'$gt': datetime.strptime('2015-12-31 16:00:00', '%Y-%m-%d %H:%M:%S'),
            '$lt': datetime.strptime('2016-07-31 16:00:00', '%Y-%m-%d %H:%M:%S')},'chn':{'$in': CHN_LIST}})
        for user_stats in users:
            uid = user_stats['_id']
            if redis_cache.is_virtual_account(uid):
                continue
            if not user_stats.get('updated_at') or not user_stats.get('created_at'):
                continue
            chn = user_stats['chn']
            chn_conf = chn_dict[chn]
            create_month = datetime.strftime(user_stats.get('created_at'), '%Y-%m')
            chn_conf.setdefault(create_month, {'total_count': 0, 'total_life_day': 0,
                'total_recharge_amount': 0, 'total_recharge_count': 0, 'monthly_recharge': {}})
            month_conf = chn_conf[create_month]
            recharge_stats = user_stats.get('recharge', {})
            recharge_total = int(recharge_stats.get('total', 0))
            recharge_count = int(recharge_stats.get('count', 0))
            life_days = (user_stats['updated_at'] - user_stats['created_at']).days
            month_conf['total_count'] += 1
            month_conf['total_life_day'] += life_days 
            month_conf['total_recharge_amount'] += recharge_total
            month_conf['total_recharge_count'] += recharge_count
            # daily stats
            monthly_recharge = month_conf['monthly_recharge']
            daily_stats = db.daily_stats.find({'user_id': uid, 'recharge': {'$exists': 1}})
            for daily_stat in daily_stats:
                recharge_stats = daily_stat.get('recharge', {})
                recharge_total = int(recharge_stats.get('total', 0))
                recharge_count = int(recharge_stats.get('count', 0))
                month_str = datetime.strftime(daily_stat['updated_at'], '%Y-%m')
                m_entry = monthly_recharge.setdefault(month_str, [0, 0])
                m_entry[0] += recharge_count
                m_entry[1] += recharge_total
            print 'finish uid:%s chn:%s' % (uid, chn)
        print chn_dict
    if cmd == 'dumps':
        fp = open('./chn_stats.json', 'r')
        text = fp.read().strip()
        chn_stats = json.loads(text)
        print chn_stats
        for chn, conf in chn_stats.items():
            for month,v in conf.items():
                #average_days = float(v['total_life_day']) / v['total_count']
                #print '%s\t%s\t%s\t%s\t%s\t%s' % (chn, month, average_days, v['total_count'], v['total_recharge_amount'], v['total_recharge_count'])
                m_dict = v['monthly_recharge']
                for mm, entry in m_dict.items():
                    print '%s\t%s\t%s\t%s\t%s\t%s' % (chn, month, v['total_count'], mm, entry[0], entry[1])
