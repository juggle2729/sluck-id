# -*- coding: utf-8 -*-
from __future__ import absolute_import

import datetime
import json
import os
import sys

import tablib

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.model import orm
from luckycommon.model.pay import Pay, PayType
from luckycommon.model.transaction import Transaction, TRANSACTION_TYPE
from luckycommon.account.model.account import Account, AccountThird
from luckycommon.account.db import account as account_db
from luckycommon.db import activity as activity_db
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.mail import TOOL_MAIL_SENDER
from pymongo import MongoClient

from django.conf import settings

db = MongoClient(settings.MONGO_ADDR).lucky
EXPORT_PATH = '/home/ubuntu/af-env/data/stats/'


def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path


def history_data(last_days=16):
    html_str = '<html><head></head><body>'
    for delta_day in range(1, last_days):
        html_str += get_today_new(delta_day)
        html_str += '<hr>'
        print delta_day
    html_str += '</body></html>'
    return html_str


def get_agent_stats():
    accounts = Account.query.filter(Account.is_virtual == 1).all()
    v_list = []
    for account in accounts:
        uid = account.id
        nick_name = account.nick_name
        avatar_id = account.avatar_id
        register_time = account.created_at.strftime('%Y-%m-%d %H:%M:%S')
        account_token = account_db.get_online_info(uid)
        token_extend = json.loads(account_token.extend)
        ip, addr = token_extend.get('ip'), token_extend.get('addr')
        items = orm.session.query(Transaction.price).filter(Transaction.user_id == uid) \
            .filter(Transaction.type == TRANSACTION_TYPE.BALANCE_BUY).all()
        consume_price = 0
        consume_count = 0
        for item in items:
            price = item[0]
            consume_count += 1
            consume_price += price
        winned_list = redis_cache.get_winn_list(uid)
        win_count = len(winned_list)
        win_price = 0
        big_win_count = 0
        big_win_price = 0
        winned_activitys = activity_db.get_activitys_by_ids(winned_list, need_fill=False)
        for a in winned_activitys:
            win_price += a.target_amount
            if a.target_amount > 3000:
                big_win_count += 1
                big_win_price += a.target_amount
        v_list.append((uid, nick_name, avatar_id, register_time, ip, addr, consume_count, consume_price,
                       win_count, win_price, big_win_count))
        print 'finished agent %s' % uid
    excel_header = [u'uid', u'昵称', u'头像', u'注册时间', u'IP地址', u'IP位置', u'参与次数', u'参与人次', u'中奖次数', u'中奖金额', u'价值大于3000商品中奖次数']
    file_path = redirect_to_file(v_list, excel_header, u'top_agent.xlsx')
    TOOL_MAIL_SENDER.send(u"自有用户全量数据", u'详情请见附件', attachments=[file_path])


def get_today_top_user(delta_day=1, top_count=30):
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=delta_day)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now - datetime.timedelta(days=delta_day - 1)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    items = list(db.daily_stats.find({
        "updated_at": {"$lt": end_date, "$gte": start_date},
        "recharge.total": {"$gt": 0}
    }).sort([("recharge.total", -1)]).limit(top_count))
    top_list = []
    for item in items:
        uid = item['user_id']
        acc = Account.query.filter(Account.id == uid).first()
        nick_name = acc.nick_name
        phone = acc.phone
        email = acc.email
        user_stats = db.user_stats.find_one({'_id': uid})
        created_at = user_stats['created_at']
        top_list.append((
            uid,
            nick_name,
            phone,
            email,
            created_at.strftime('%Y-%m-%d %H:%M:%S'),
            item['recharge']['total'] if 'recharge' in item else 0,
            item['recharge']['count'] if 'recharge' in item else 0,
            item['pay']['count'] if 'pay' in item else 0,
            item['pay']['total'] if 'pay' in item else 0,
            item['win']['count'] if 'win' in item else 0,
            item['win']['total'] if 'win' in item else 0
        ))
    top_list.sort(key=lambda x: x[2], reverse=True)
    excel_header = [u'uid', u'nick_name', u'phone', u'email', u'注册时间', u'充值额度', u'充值册数', u'消费次数', u'消费人次', u'中奖次数', u'中奖金额']
    file_path = redirect_to_file(top_list, excel_header, u'daily_top_data_%s.xlsx' % start_date.strftime('%Y-%m-%d'))
    TOOL_MAIL_SENDER.send(u"今日渠道用户充值top30", u'详情请见附件', attachments=[file_path])


def get_today_new(delta_day=1):
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=delta_day)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now - datetime.timedelta(days=delta_day - 1)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    items = db.user_stats.find({'$and': [{'created_at': {'$gte': start_date}}, {'created_at': {'$lte': end_date}}]})
    total_bingo_list = []
    total_pay_one_list = []
    total_recharge_list = []
    total_recharge_amount = 0
    total_recharge_count = 0
    total_user_count = 0
    today_chn_dict = {}
    for item in items:
        total_user_count += 1
        user_id = item['_id']
        chn = item.get('chn', 'none')
        account_third = AccountThird.query.filter(AccountThird.account_id == user_id).first()
        if account_third:
            chn = 'uxin'
        today_chn_dict.setdefault(chn,
                                  {'bingo_list': [], 'pay_one_list': [], 'recharge_list': [], 'recharge_count': 0, 'recharge_amount': 0,
                                   'user_count': 0})
        bingo_list = today_chn_dict[chn]['bingo_list']
        pay_one_list = today_chn_dict[chn]['pay_one_list']
        recharge_list = today_chn_dict[chn]['recharge_list']
        today_chn_dict[chn]['user_count'] += 1
        created_at = item['created_at']
        updated_at = item['updated_at']
        if created_at.day != updated_at.day:
            bingo_list.append(user_id)
            total_bingo_list.append(user_id)
        if item.get('pay') and item['pay'].get('count') and item['pay']['count'] == 1:
            pay_one_list.append(user_id)
            total_pay_one_list.append(user_id)
        if item.get('recharge') and item['recharge'].get('total') and item['recharge']['total'] > 0:
            recharge_list.append({user_id: item['recharge']['total']})
            total_recharge_list.append({user_id: item['recharge']['total']})
            today_chn_dict[chn]['recharge_amount'] += item['recharge']['total']
            today_chn_dict[chn]['recharge_count'] += item['recharge']['count']
            total_recharge_amount += item['recharge']['total']
            total_recharge_count += item['recharge']['count']

    html_str = u'<h2>今日数据</h2> <br /> date: %s -- %s<br />' % (utc_to_local_str(start_date), utc_to_local_str(end_date))
    # total
    pay_items = Pay.query.filter(Pay.status == 2).filter(Pay.updated_at > start_date).filter(Pay.updated_at < end_date).all()
    chn_dict = {}
    total_recharge = 0
    total_count = 0
    total_users = set()
    pay_dict = {}
    for item in pay_items:
        pay_type = item.pay_type
        pay_dict.setdefault(pay_type, 0)
        user_id = item.user_id
        price = item.price
        try:
            pay_dict[pay_type] += price
        except:
            print item.id
        total_recharge += price
        total_count += 1
        total_users.add(user_id)
        user_stats = db.user_stats.find_one({'_id': user_id})
        if not user_stats:
            continue
        chn = user_stats.get('chn', 'none')
        if chn == 'uxin':
            item = Account.query.filter(Account.id == user_id).one()
            if item.password:
                chn = 'uxin-app'
        chn_dict.setdefault(chn, {'amount': 0, 'users': set(), 'count': 0})
        chn_dict[chn]['amount'] += price
        chn_dict[chn]['count'] += 1
        chn_dict[chn]['users'].add(user_id)
    html_str += u'<hr><h3>渠道数据</h2><br />总充值金额:%s 人数:%s 次数:%s<br />' % (total_recharge, len(total_users), total_count)
    for pay_type, pay_price in pay_dict.items():
        html_str += u'支付方式: %s  支付金额: %s<br />' % (PayType.get_name(pay_type), pay_price)
    html_str += u'<table border="1"><tr><td>日期</td><td>渠道</td>\
                                        <td>新增</td>\
                                        <td>活跃</td>\
                                        <td>注册人数</td>\
                                        <td>参与1次人数</td>\
                                        <td>新用户充值人数</td>\
                                        <td>新用户充值次数</td>\
                                        <td>新用户充值金额</td>\
                                        <td>总充值人数</td>\
                                        <td>总充值次数</td>\
                                        <td>总充值金额</td></tr>'
    date_str = utc_to_local_str(start_date).split(' ')[0]
    for chn, info in chn_dict.items():
        active_count = db.user_stats.count({'chn': chn, 'updated_at': {'$gte': start_date}})
        new_device_count = db.device_stats.count(
            {'chn': chn, '$and': [{'created_at': {'$gte': start_date}}, {'created_at': {'$lte': end_date}}]})
        today_info = today_chn_dict.get(chn) or {'user_count': 0, 'pay_one_list': [], 'recharge_list': [], 'recharge_count': 0,
                                                 'recharge_amount': 0}
        html_str += u'<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            date_str, chn, new_device_count, active_count,
            today_info['user_count'], len(today_info['pay_one_list']), len(today_info['recharge_list']),
            today_info['recharge_count'], today_info['recharge_amount'], len(info['users']), info['count'], info['amount'])
    html_str += u'<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        date_str, u'总计',
        '--', '--', total_user_count, len(total_pay_one_list), len(total_recharge_list), total_recharge_count, total_recharge_amount,
        len(total_users), total_count, total_recharge)
    html_str += '</table>'
    return html_str


def get_yesterday_active():
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=2)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now - datetime.timedelta(days=1)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    items = db.user_stats.find({'$and': [{'created_at': {'$gte': start_date}}, {'created_at': {'$lte': end_date}}]})
    total_bingo_list = []
    total_user_count = 0
    chn_dict = dict()
    for item in items:
        total_user_count += 1
        user_id = item['_id']
        chn = item.get('chn', 'none')
        account_third = AccountThird.query.filter(AccountThird.account_id == user_id).first()
        if account_third:
            chn = 'uxin'
        chn_dict.setdefault(chn, {'bingo_list': [], 'user_count': 0})
        chn_dict[chn]['user_count'] += 1
        bingo_list = chn_dict[chn]['bingo_list']
        created_at = item['created_at']
        updated_at = item['updated_at']
        if created_at.day != updated_at.day:
            bingo_list.append(user_id)
            total_bingo_list.append(user_id)
    html_str = u'<hr> <h2>前日留存</h2> <br /> date: %s -- %s<br />' % (utc_to_local_str(start_date), utc_to_local_str(end_date))
    for chn, info in chn_dict.items():
        html_str += u'渠道：%s, 新增注册人数:%s, 活跃人数:%s, 次日留存:%s%% <br />' % (chn, info['user_count'],
                                                                      len(info['bingo_list']),
                                                                      round(float(len(info['bingo_list'])) * 100 / info['user_count'], 2))
    html_str += u'总计, 新增人数:%s, 活跃人数:%s, 次日留存:%s%% <br />' % (total_user_count, len(total_bingo_list),
                                                             '--' if not total_user_count else round(
                                                                 (float(len(total_bingo_list)) / total_user_count) * 100, 2))
    return html_str


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'new':
        html_str = '<html><head></head><body>'
        html_str += get_today_new()
        html_str += get_yesterday_active()
        html_str += '</body></html>'
        # print html_str
        TOOL_MAIL_SENDER.send(u"[%s]今日新增&&前日留存" % settings.REGION, html_str)
    if cmd == 'top':
        get_today_top_user()
    if cmd == 'history':
        html_str = history_data(last_days=18)
        TOOL_MAIL_SENDER.send("历史数据", html_str)
    if cmd == "pay":
        dd = sys.argv[2]
        now = datetime.datetime.strptime(dd, '%Y-%m-%d')
        start_date = now - datetime.timedelta(days=3)
        start_date = start_date.replace(hour=0)
        end_date = now - datetime.timedelta(days=2)
        end_date = end_date.replace(hour=0)
        pay_items = Pay.query.filter(Pay.updated_at >= start_date.strftime('%Y-%m-%d %H:%M:%S')) \
            .filter(Pay.updated_at <= end_date.strftime('%Y-%m-%d %H:%M:%S')) \
            .filter(Pay.status == 2).all()
        total_amount = 0
        total_count = 0
        user_set = set()
        uxin_user_set = set()
        uxin_count = 0
        uxin_amount = 0
        for item in pay_items:
            total_amount += item.price
            total_count += 1
            user_id = item.user_id
            user_set.add(user_id)
            account_third = AccountThird.query.filter(AccountThird.account_id == user_id).first()
            if account_third:
                uxin_amount += item.price
                uxin_count += 1
                uxin_user_set.add(user_id)
        print 'date: %s -- %s' % (start_date, end_date)
        print 'amount:%s, count:%s, user_count:%s' % (total_amount, total_count, len(user_set))
        print 'uxin amount:%s, count:%s, user_count:%s' % (uxin_amount, uxin_count, len(uxin_user_set))
    if cmd == "register":
        dd = sys.argv[2]
        now = datetime.datetime.strptime(dd, '%Y-%m-%d')
        start_date = now - datetime.timedelta(days=3)
        start_date = start_date.replace(hour=0)
        end_date = now - datetime.timedelta(days=2)
        end_date = end_date.replace(hour=0)
        account_items = Account.query.filter(Account.created_at >= start_date.strftime('%Y-%m-%d %H:%M:%S')) \
            .filter(Account.created_at <= end_date.strftime('%Y-%m-%d %H:%M:%S')) \
            .all()
        total_count = 0
        uxin_count = 0
        for item in account_items:
            user_id = item.id
            total_count += 1
            account_third = AccountThird.query.filter(AccountThird.account_id == user_id).first()
            if account_third:
                uxin_count += 1
        print 'date: %s -- %s' % (start_date, end_date)
        print 'register: total:%s, uxin:%s' % (total_count, uxin_count)
    if cmd == 'agent':
        get_agent_stats()
