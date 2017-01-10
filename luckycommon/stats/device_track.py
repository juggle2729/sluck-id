# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from luckycommon.stats import MG as mg
from luckycommon.account.db.account import get_account
from luckycommon.utils.tz import get_utc_date
from luckycommon.utils.decorator import mongo_wrapper
from luckyadmin.stats.helper import list_object


@mongo_wrapper
def create_device_track(info):
    """
        params: {
            "aid": 'xxxxxxxxxxxx', # android device id
            "type": 'htc',         # android machine brand,
            "run_count": 10       # app open count,
            "uid":  123456         # optional, last registered user
            "reason": []           # reason
        }
        extra need data: {
            "created_at": '2016-06-20 10:00:00', # first run time for this aid
            "remove_at": '2016-06-21 10:00:00',  # last uninstall time
            "total_pay": 0                       # pay.total from user_stats
        }
    """
    info['remove_at'] = datetime.utcnow()
    stats = {}
    aid = info.pop('aid')
    if info.get('uid'):
        stats = mg.user_stats.find_one({'_id': info['uid']}) or {}
    info['total_pay'] = stats.get('pay', {}).get('total', 0)
    mg.device_stats.update({'_id': aid}, {'$set': info}, upsert=True)
    k = mg.device_stats.find_one({'_id': aid})
    if 'created_at' not in k:
        calc_info = {}
        if 'created_at' in stats:
            calc_info['created_at'] = stats['created_at']
        elif 'uid' in info:
            account = get_account(info['uid'])
            if account is not None:
                calc_info['created_at'] = account.created_at
        if not calc_info:
            calc_info['created_at'] = info['remove_at']
        mg.device_stats.update({'_id': aid}, {'$set': calc_info})


@mongo_wrapper
def update_uninstall_reason(info):
    aid = info.pop('aid')
    mg.device_stats.update({'_id': aid}, {'$set': info}, upsert=True)


@mongo_wrapper
def list_device_stats(query_dct):
    return list_object(query_dct, mg.device_stats)


@mongo_wrapper
def calc_questionare_overview():
    info = {
        'total_count': mg.device_stats.count({'reason': {'$exists': True}}),
        'dist': {}
    }
    for k in range(1, 11):
        info['dist'][k] = mg.device_stats.count({'reason': str(k)})
    return info


@mongo_wrapper
def calc_uninstall_overview(date=None):
    if date is None:
        date = get_utc_date()
    end_date = date + timedelta(days=1)
    info = {
        'total_count': mg.device_stats.count({'remove_at': {'$exists': True}}),
        'today_count': mg.device_stats.count(
            {'remove_at': {'$gte': date, '$lt': end_date}}),
        'pay_count': mg.device_stats.count({'total_pay': {'$gt': 0}})
    }
    temp = mg.device_stats.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$run_count'}}}])
    temp = temp.next() if temp.alive else {}
    info['run_count'] = temp.get('total', 0)

    return info
