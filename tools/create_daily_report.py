# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
from sqlalchemy import func, text
from datetime import timedelta


# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.stats import MG as mg
from luckycommon.utils.tz import get_utc_date, local_now, utc_to_local
from luckycommon.model import slave
from luckycommon.model.activity import ACTIVITY_STATUS, Activity
from luckycommon.model.stock import Goods
from luckycommon.account.model.account import Account
from luckycommon.model.coupon import AccountCoupon, COUPON_STATUS
from luckycommon.model.transaction import Transaction, TRANSACTION_TYPE
from luckycommon.credit.model.credit import CreditRecord


def create_daily_report(day):
    end = day + timedelta(days=1)
    value = {}
    # 新增设备
    t = mg.device_stats.aggregate([
        {"$match": {"created_at": {"$gte": day, "$lt": end}}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    t = t.next() if t.alive else {}
    value['new_device'] = t.get('count', 0)
    # 活跃设备
    t = mg.device_stats.aggregate([
        {"$match": {"updated_at": {"$gte": day}}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    t = t.next() if t.alive else {}
    value['active_device'] = t.get('count', 0)
    # 新用户
    t = mg.user_stats.aggregate([
        {"$match": {"created_at": {"$gte": day, "$lt": end}}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    t = t.next() if t.alive else {}
    value['new_user'] = t.get('count', 0)
    # 活跃用户
    t = mg.user_stats.aggregate([
        {"$match": {"updated_at": {"$gte": day}}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    t = t.next() if t.alive else {}
    value['active_user'] = t.get('count', 0)
    # 总付费（充值）人数/金额
    t = mg.daily_stats.aggregate([
        {"$match": {"$and": [
            {"updated_at": {"$gte": day, "$lt": end}},
            {"recharge.total": {"$gt": 0}}
        ]}},
        {"$group": {"_id": None, "total": {"$sum": 1},
                    "price": {"$sum": "$recharge.total"}}}
    ])
    t = t.next() if t.alive else {}
    value['recharge_user'] = t.get('total', 0)
    value['recharge_price'] = t.get('price', 0)
    # 渠道用户参与人数/金额
    t = mg.daily_stats.aggregate([
        {"$match": {"$and": [
            {"updated_at": {"$gte": day, "$lt": end}},
            {"pay.total": {"$gt": 0}}
        ]}},
        {"$group": {"_id": None, "total": {"$sum": 1},
                    "price": {"$sum": "$pay.total"}}}
    ])
    t = t.next() if t.alive else {}
    value['pay_user'] = t.get('total', 0)
    value['pay_price'] = t.get('price', 0)
    # 新用户付费人数/金额
    t = mg.daily_stats.aggregate([
        {"$match": {"$and": [
            {"created_at": {"$gte": day, "$lt": end}},
            {"recharge.total": {"$gt": 0}}
        ]}},
        {"$group": {"_id": None, "total": {"$sum": 1},
                    "price": {"$sum": "$recharge.total"}}}
    ])
    t = t.next() if t.alive else {}
    value['new_recharge_user'] = t.get('total', 0)
    value['new_recharge_price'] = t.get('price', 0)
    # 真实用户中奖人数/金额
    t = mg.daily_stats.aggregate([
        {"$match": {"$and": [
            {"updated_at": {"$gte": day, "$lt": end}},
            {"win.total": {"$gt": 0}}
        ]}},
        {"$group": {"_id": None, "total": {"$sum": 1},
                    "price": {"$sum": "$win.total"}}}
    ])
    t = t.next() if t.alive else {}
    value['real_win_count'] = t.get('total', 0)
    value['real_win_price'] = t.get('price', 0)
    # 商品开奖数/平均开奖时间
    t = slave.session.query(
        func.count(Activity.id),
        func.sum(func.timestampdiff(
            text('SECOND'),
            Activity.created_at, Activity.announced_at))).filter(
        Activity.status == ACTIVITY_STATUS.ANNOUNCED).filter(
        Activity.announced_at >= day).filter(
        Activity.announced_at < end).first()
    value['announced_activity'], value['total_buy_time'] = t
    if value['total_buy_time'] is None:
        value['total_buy_time'] = 0
    if value['announced_activity'] > 0:
        value['total_buy_time'] = int(float(value['total_buy_time'])) - 180
    # 开奖金额（商品金额）
    t = slave.session.query(func.sum(Goods.price)).join(
        Activity, Goods.id == Activity.goods_id).filter(
        Activity.status == ACTIVITY_STATUS.ANNOUNCED).filter(
        Activity.announced_at >= day).filter(
        Activity.announced_at < end).scalar() or 0
    value['announced_price'] = int(float(t))
    # 虚拟用户中奖人数/金额
    value['virtual_win_count'] = value[
        'announced_activity'] - value['real_win_count']
    value['virtual_win_price'] = value[
        'announced_price'] - value['real_win_price']
    # 总体利润：(真实用户充值金额 + 虚拟用户消费金额) - 全部开奖的成本
    t = slave.session.query(func.sum(Transaction.price)).join(
        Account, Account.id == Transaction.user_id).filter(
        Transaction.status == 1).filter(
        Transaction.type == TRANSACTION_TYPE.BALANCE_BUY).filter(
        Transaction.created_at >= day).filter(
        Transaction.created_at < end).filter(
        Account.is_virtual == True).scalar() or 0
    t = abs(int(float(t)))
    value['virtual_pay_price'] = t
    value['total_recharge'] = value['recharge_price'] + t
    value['total_profit'] = value['recharge_price'] + \
        t - value['announced_price']
    value['total_profit_rate'] = value['total_profit'] / value[
        'total_recharge'] if value['total_recharge'] else 0
    # 实际利润: 真实用户充值 - 真实用户中奖成本
    value['real_profit'] = value['recharge_price'] - value['real_win_price']
    value['real_profit_rate'] = value['real_profit'] / value[
        'recharge_price'] if value['recharge_price'] else 0

    mg.daily_report.update_one({'_id': utc_to_local(day).strftime('%Y-%m-%d')},
                               {'$set': value}, upsert=True)


def update_stay_2_count(d):
    e = d + timedelta(days=1)
    t = mg.device_stats.aggregate([
        {'$match': {'$and': [
            {'created_at': {'$gte': d, "$lt": e}},
            {'updated_at': {'$gt': e}}
        ]}},
        {'$group': {'_id': None, 'count': {'$sum': 1}}}
    ])
    t = t.next() if t.alive else {}
    mg.daily_report.update_one({'_id': utc_to_local(d).strftime('%Y-%m-%d')},
                               {'$set': {'stay_2': t.get('count', 0)}})


def main():
    today = get_utc_date()
    yesterday = today - timedelta(days=1)
    day = today
    now = local_now()
    if now.hour == 16:
        day = yesterday
    update_day = day - timedelta(days=1)
    print now, 'updating daily_report for utc time %s...' % day
    create_daily_report(day)
    if now.hour % 2 == 0:
        print local_now(), 'updating stay...'
        update_stay_2_count(update_day)
    print local_now(), 'calc complete.'


if __name__ == '__main__':
    main()
