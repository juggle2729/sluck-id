# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from django.views.decorators.http import require_GET

from luckycommon.stats import MG as mg
from luckycommon.utils.tz import local_now, get_utc_date, utc_to_local
from luckycommon.utils.decorator import mongo_wrapper, response_wrapper
from luckycommon.utils.api import token_required

_LOGGER = logging.getLogger(__name__)

CACHED_DAY = {}


def get_time_interval():
    today = get_utc_date()
    global CACHED_DAY
    if today in CACHED_DAY:
        return CACHED_DAY.get(today)
    yesterday = today - timedelta(days=1)
    two_days_ago = yesterday - timedelta(days=1)
    now = local_now()
    last_monday = get_utc_date(
        (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d'))
    t = (now - timedelta(days=now.day - 1)) if now.day != 1 else now
    last_month_1st = get_utc_date(t.strftime('%Y-%m-%d'))
    CACHED_DAY = {
        today: {
            'today': today,
            'yesterday': yesterday,
            'two_days_ago': two_days_ago,
            'this_week': last_monday,
            'this_month': last_month_1st
        }
    }
    return CACHED_DAY[today]


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_user_overview(req):
    data = {
        'today': {},
        'yesterday': {},
        'this_month': {},
        'all': {}
    }
    date_param = get_time_interval()
    _LOGGER.debug('parameters are: %s' % date_param)
    # 今日/昨日数据
    for d in "today", "yesterday":
        key = utc_to_local(date_param[d]).strftime('%Y-%m-%d')
        report = mg.daily_report.find_one({"_id": key})
        if report:
            for k in ('new_device', 'new_user', 'active_user',
                      'active_device', 'recharge_user', 'recharge_price'):
                data[d][k] = report.get(k, 0)
    # 本月
    # 新增设备:
    start = date_param['this_month']
    data['this_month']['new_device'] = mg.device_stats.count(
        {"created_at": {"$gte": start}})
    # 活跃设备
    data['this_month']['active_device'] = mg.device_stats.count(
        {"updated_at": {"$gte": start}})
    # 新用户
    data['this_month']["new_user"] = mg.user_stats.count(
        {"created_at": {"$gte": start}})
    # 活跃用户
    data['this_month']["active_user"] = mg.user_stats.count({
        "updated_at": {"$gte": start}})
    # 本月付费人数
    t = mg.daily_stats.aggregate([
        {"$match": {"$and": [
            {"updated_at": {"$gte": start}},
            {"recharge.total": {"$gt": 0}}
        ]}},
        {"$group": {"_id": "$user_id"}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    t = t.next() if t.alive else {}
    data["this_month"]["recharge_user"] = t.get('count', 0)
    # 本月付费金额
    t = mg.daily_stats.aggregate([
        {"$match": {"updated_at": {"$gte": start}}},
        {"$group": {"_id": None, "price": {"$sum": "$recharge.total"}}}
    ])
    t = t.next() if t.alive else {}
    data["this_month"]["recharge_price"] = t.get("price", 0)
    # 累计数据
    # 累计新增设备 = 累计活跃设备
    # 累计新增用户 = 累计活跃用户, 因此活跃数据无意义
    data['all']['active_device'] = data['all'][
        'new_device'] = mg.device_stats.count()
    data['all']['active_user'] = data['all'][
        'new_user'] = mg.user_stats.count()
    t = mg.user_stats.aggregate([
        {'$match': {'recharge.total': {'$gt': 0}}},
        {'$group': {'_id': None, 'count': {'$sum': 1},
                    'price': {'$sum': '$recharge.total'}}}
    ])
    t = t.next() if t.alive else {}
    data['all']['recharge_user'] = t.get('count', 0)
    data['all']['recharge_price'] = t.get('price', 0)
    return data


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_activity_overview(req):
    date_param = get_time_interval()
    data = {
        'today': {},
        'yesterday': {},
        'this_month': {},
        'all': {}
    }
    fields = ('announced_activity', 'announced_price',
              'total_buy_time', 'real_win_count', 'real_win_price')
    # 今日/昨日数据
    for d in 'today', 'yesterday':
        t = mg.daily_report.find_one(
            {'_id': utc_to_local(date_param[d]).strftime('%Y-%m-%d')})
        if t:
            for k in fields:
                data[d][k] = t.get(k, 0)

    # 本月数据
    group = {'_id': None}
    for k in fields:
        group[k] = {'$sum': '$%s' % k}
    t = mg.daily_report.aggregate([
        {'$match': {'_id': {'$gte': utc_to_local(
            date_param['this_month']).strftime('%Y-%m-%d')}}},
        {'$group': group}
    ])
    t = t.next() if t.alive else {}
    t.pop('_id', None)
    for k in fields:
        t[k] = t.get(k, 0) + data['today'][k]
    data['this_month'] = t
    # 累计数据
    t = mg.daily_report.aggregate([
        {'$group': group}
    ])
    t = t.next() if t.alive else {}
    t.pop('_id', None)
    data['all'] = t

    return data


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_cost_overview(req):
    date_param = get_time_interval()
    data = {
        'today': {},
        'yesterday': {},
        'this_month': {},
        # 'all': {}
    }
    fields = ('announced_price', 'total_recharge', 'total_profit',
              'recharge_price', 'real_win_price', 'real_profit')
    # 今日/昨日数据
    for d in 'today', 'yesterday':
        t = mg.daily_report.find_one(
            {'_id': utc_to_local(date_param[d]).strftime('%Y-%m-%d')})
        if t:
            for k in fields:
                data[d][k] = t.get(k, 0)

    # 本月数据
    group = {'_id': None}
    for k in fields:
        group[k] = {'$sum': '$%s' % k}
    t = mg.daily_report.aggregate([
        {'$match': {'_id':
                    {'$gte': utc_to_local(
                        date_param['this_month']).strftime('%Y-%m-%d')}}},
        {'$group': group}
    ])
    t = t.next() if t.alive else {}
    t.pop('_id', None)
    data['this_month'] = t
    # 累计数据
    # t = mg.daily_report.aggregate([
    #     {'$group': group}
    # ])
    # t = t.next() if t.alive else {}
    # for k in fields:
    #     t[k] = t.get(k, 0) + data['today'][k]
    # t.pop('_id', None)
    # data['all'] = t

    return data
