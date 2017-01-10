# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from django.views.decorators.http import require_GET

from luckycommon.stats import MG as mg
from luckycommon.utils.tz import get_utc_date, utc_to_local_str
from luckycommon.utils.decorator import mongo_wrapper, response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger(__name__)


def _get_date_range(query_dct, is_key=False):
    # date_range 使用逗号分割
    # 如果是key的话，无需转换时区， 返回字符串数组
    # 否则，返回转换时区后的datetime数组
    date_range = query_dct.get('date_range', '')
    if not date_range:
        raise ParamError('date_range missed')
    date_range = date_range.split(',')
    if is_key:
        today = get_utc_date().strftime('%Y-%m-%d')
        if len(date_range) == 1:
            date_range.append(today)
        return date_range

    # 用于updated_at等具体时间的搜索
    now = datetime.utcnow()
    date_range[0] = get_utc_date(date_range[0])
    if len(date_range) == 1:
        date_range.append(now)
    else:
        date_range[1] = get_utc_date(date_range[1])
    if date_range[0] > now:
        raise ParamError['future is not coming']
    if date_range[0] > date_range[1] or date_range[1] > now:
        date_range[1] = now
    date_range[1] += timedelta(days=1)
    return date_range


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_daily_report(req):
    query_dct = req.GET.dict()
    date_range = _get_date_range(query_dct, is_key=True)
    data_type = query_dct.get('type')
    items = mg.daily_report.find(
        {'_id': {'$gte': date_range[0], '$lte': date_range[1]}})
    resp_items = []
    for item in items:
        if data_type is None:               # full list
            if item.get('new_device', 0) > 0:
                item['register_rate'] = round(
                    float(item['new_user']) / item['new_device'], 4)
                item['stay_2_rate'] = round(
                    float(item.get('stay_2', 0)) / item['new_device'], 4)
            else:
                item['register_rate'] = item['stay_2_rate'] = 0
            if item['new_user'] > 0:
                item['new_recharge_rate'] = round(
                    float(item['new_recharge_user']) / item['new_user'], 4)
            else:
                item['new_recharge_rate'] = 0
            if item['active_user'] > 0:
                item['recharge_rate'] = round(
                    float(item['recharge_user']) / item['active_user'], 4)
            else:
                item['recharge_rate'] = 0
            resp_items.append(item)
        elif data_type == 'profit':
            data = {
                'recharge_price': item['recharge_price'],
                'real_win_price': item['real_win_price'],
                'real_profit': item['real_profit'],
                'real_profit_rate': round(item['real_profit_rate'], 4)
            }
            resp_items.append(data)

    return {'list': resp_items}


def _find_range(ranges, num):
    # 二分搜索数据所在区间，假设区间已经排序
    if not ranges:
        return None
    mid = len(ranges) / 2
    r = ranges[mid]
    if r[1] is not None:
        if num > r[1]:
            return _find_range(ranges[mid + 1:], num)
        elif num == r[1]:
            return r        # 落在此区间
        else:
            if r[0] is None:
                return r
            else:
                if num >= r[0]:
                    return r
                else:
                    return _find_range(ranges[:mid], num)
    else:
        if num >= r[0]:
            return r
        else:
            return _find_range(ranges[:mid], num)


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_recharge_report(req):
    query_dct = req.GET.dict()
    user_type = int(query_dct.get('user_type', -1))
    date_range = _get_date_range(query_dct, is_key=True)

    if date_range[0] == date_range[1]:
        key = date_range[0]
        table = mg.recharge_report
        if user_type == 1:
            # 新用户
            table = mg.fresh_recharge_report
        data = table.find_one({'_id': key}) or {}
        return data
    intervals = [(1, 2), (3, 10), (11, 50), (51, 100), (101, 500),
                 (501, 1000), (1001, 2000), (2001, 4000), (4001, 8000),
                 (8001, 15000), (15000, None)]
    if user_type == 1:
        items = mg.fresh_recharge_report.find({'_id': {
            '$gte': date_range[0],
            '$lte': date_range[1]
        }})
        data = {}
        # 新用户数据，直接聚合
        for item in items:
            for k, v in item.iteritems():
                if k == '_id':
                    data[k] = v
                elif isinstance(v, dict):
                    data.setdefault(k, {})
                    for ik, iv in v.iteritems():
                        data[k].setdefault(ik, 0)
                        data[k][ik] += iv
                else:
                    data.setdefault(k, 0)
                    data[k] += v
        return data
    else:
        # 所有用户数据, 只能实时聚合, 可能需要分页进行优化
        # 从daily_stats里面重新计算recharge_count, recharge_price,
        # gain_count, win_count, lose_count
        fields = ('recharge_count', 'recharge_price', 'gain_count',
                  'win_count', 'lose_count')
        data = {}
        for k in fields:
            data[k] = 0
        for k in intervals:
            key = '%s-%s' % (k[0], k[1])
            for f in fields:
                data.setdefault(key, {})[f] = 0
        date_range = _get_date_range(query_dct)
        items = mg.daily_stats.aggregate([
            {'$match': {'updated_at': {
                        '$gte': date_range[0], '$lt': date_range[1]}}},
            {'$group': {'_id': '$user_id', 'win': {'$sum': '$win.total'},
                        'recharge': {'$sum': '$recharge.total'}}},
            {'$match': {'recharge': {'$gte': 1}}}
        ])
        for item in items:
            recharge = item.get('recharge')
            data['recharge_count'] += 1
            data['recharge_price'] += recharge
            interval = _find_range(intervals, recharge)
            key = '%s-%s' % (interval[0], interval[1])
            data[key]['recharge_count'] += 1
            data[key]['recharge_price'] += recharge
            win = item.get('win', 0)
            if win > 0:
                data['win_count'] += 1
                data[key]['win_count'] += 1
            if win - recharge > 0:
                data['gain_count'] += 1
                data[key]['gain_count'] += 1
            else:
                data['lose_count'] += 1
                data[key]['lose_count'] += 1

        return data


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_tactics_report(req):
    query_dct = req.GET.dict()
    date_range = _get_date_range(query_dct)
    recharge_range = query_dct.get('recharge_range', '')
    data = {
        'count': 0,
        'amount': 0
    }
    ranges = [(None, -10001), (-10000, -5001), (-5000, -2001), (-2000, -1001),
              (-1000, -501), (-500, -201), (-200, -1), (0, 200), (201, 500),
              (501, 1000), (1001, 2000), (2001, 5000), (5001, 10000),
              (10000, None)]
    for r in ranges:
        key = '%s ~ %s' % (r[0], r[1])
        data[key] = {
            'count': 0,
            'amount': 0
        }
    extra = {}
    if recharge_range:
        recharge_range = recharge_range.split(',')
        extra = {'recharge': {}}
        if len(recharge_range) == 1:
            extra['recharge']['$gte'] = int(recharge_range[0])
        else:
            extra['recharge']['$lte'] = int(recharge_range[1])
    condition = [
        {'$match': {'updated_at': {
            '$gte': date_range[0], '$lt': date_range[1]
        }}},
        {'$group': {'_id': '$user_id', 'gain': {'$sum': '$gain'},
                    'recharge': {'$sum': '$recharge.total'},
                    'pay': {'$sum': '$pay.total'}}},
    ]
    if extra:
        condition.append({'$match': {'$and': [
            {'pay': {'$gt': 0}},
            extra
        ]}})
    else:
        condition.append({'$match': {'pay': {'$gt': 0}}})
    t = mg.daily_stats.aggregate(condition)
    if not t.alive:
        t = []
    for item in t:
        gain = item.get('gain', 0)
        recharge = item.get('recharge', 0)
        data['count'] += 1
        data['amount'] += recharge
        interval = _find_range(ranges, int(gain))       # 有浮点数
        key = '%s ~ %s' % (interval[0], interval[1])
        data[key]['count'] += 1
        data[key]['amount'] += recharge

    # 整理成列表
    resp_items = []
    for k in ranges:
        key = '%s ~ %s' % (k[0], k[1])
        t = data[key]
        t['id'] = key
        resp_items.append(t)
    return {'list': resp_items,
            'total': {'count': data['count'], 'amount': data['amount']}}


def _get_active_user(date_range_str):
    data = {}
    au = mg.daily_report.find(
        {'_id': {'$gte': date_range_str[0], '$lte': date_range_str[1]}},
        {'active_user': 1})
    for k in au:
        data[k['_id']] = k['active_user']
    return data

COIN_TYPE = {
    'gen_dist': {1: u'充值', 2: u'夺宝币商品', 4: u'退款', 98: u'红包',
                 99: u'元宝兑换'},
    'cost_dist': {'fee': u'话费类', 'qb': u'Q币',
                  'wechat': u'微信红包类', 'coin': u'夺宝币类'}
}

RESOURCE_DCT = {
    'coin': mg.coin_report,
    'credit': mg.credit_report,
    'coupon': mg.coupon_report
}


@mongo_wrapper
def _get_resource_report(resource, date_range):
    table = RESOURCE_DCT.get(resource)
    active_user = _get_active_user(date_range)
    items = table.find(
        {'_id': {'$gte': date_range[0], '$lte': date_range[1]}}
    )
    resp_items = []
    for item in items:
        item.pop('gen_dist', None)
        item.pop('cost_dist', None)
        item['active_user'] = active_user.get(item['_id'], 0)
        resp_items.append(item)

    result = {
        'list': resp_items,
        'gen_dist': [],
        'cost_dist': []
    }
    for k in 'gen_dist', 'cost_dist':
        items = table.aggregate([
            {'$match': {'_id': {'$gte': date_range[
                0], '$lte': date_range[1]}}},
            {'$unwind': '$' + k},
            {'$group': {'_id': '$%s.type' % k,
                        'amount': {'$sum': '$%s.amount' % k}}}
        ])
        for item in items:
            t = item.get('_id')
            if t is None:
                t = u'其他'
            if resource == 'coin':
                t = COIN_TYPE[k].get(t, t)
            result[k].append(
                {'type': t, 'amount': item.get('amount', 0)})

        result[k].sort(key=lambda v: v['amount'])
    return result


@require_GET
@response_wrapper
@token_required
def get_resource_report(req, resource):
    if resource not in RESOURCE_DCT:
        raise ParamError('resource %s not exist!' % resource)
    query_dct = req.GET.dict()
    date_range = _get_date_range(query_dct, is_key=True)
    result = _get_resource_report(resource, date_range)
    return result


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_shipping_report(req):
    query_dct = req.GET.dict()
    date_range = _get_date_range(query_dct, is_key=True)
    items = mg.shipping_report.find({'_id': {'$gte': date_range[0],
                                             '$lte': date_range[1]}})
    resp_items = []
    info = {}
    for item in items:
        for k, v in item.iteritems():
            if k == '_id':
                continue
            info.setdefault(k, {}).setdefault('count', 0)
            info[k].setdefault('amount', 0)
            info[k]['count'] += v['count']
            info[k]['amount'] += v['amount']
        resp_items.append(item)

    return {'list': resp_items, 'info': info}


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_top100_list(req):
    query_dct = req.GET.dict()
    date_range = _get_date_range(query_dct)
    items = mg.daily_stats.aggregate([
        {'$match': {'updated_at': {
            '$gte': date_range[0],
            '$lt': date_range[1]
        }}},
        {'$group': {'_id': '$user_id', 'recharge': {'$sum': '$recharge.total'},
                    'pay': {'$sum': '$pay.total'},
                    'win': {'$sum': '$win.total'},
                    'win_count': {'$sum': '$win.count'}}},
        {'$sort': {'recharge': -1}},
        {'$limit': 100}
    ])
    resp_items = []
    now = datetime.utcnow()
    rank = 0
    for item in items:
        info = mg.user_stats.find_one({'_id': item['_id']})
        if not info:
            _LOGGER.error("can't find user %s in user_stats", item['_id'])
            continue
        rank += 1
        item['rank'] = rank
        item['created_at'] = info.get('created_at', datetime.utcnow())
        item['created_at'] = utc_to_local_str(item['created_at'])
        item['lost_days'] = (now - info['updated_at']).days
        item['gain'] = item.get('win', 0) - item.get('recharge', 0)
        resp_items.append(item)

    return {'list': resp_items}
