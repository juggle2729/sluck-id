# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import tablib
import datetime
from sets import Set

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache

from luckycommon.db.account import get_account
from luckycommon.campaign.model.double_recharge_campaign import *
from luckycommon.model.coupon import AccountCoupon
from luckycommon.stats import MG as mg
from luckycommon.utils import tz
from luckycommon.utils.orm import get_count
from luckycommon.utils.mail import MailSender

mail_sender = MailSender.getInstance()
mail_sender.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@zhuohan-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@zhuohan-tech.com>',
    'to': [
           'wangfeng@zhuohan-tech.com',
           'shuxiang@zhuohan-tech.com',
           'zengyike@zhuohan-tech.com',
           'mengxiaohui@zhuohan-tech.com',
           ]
})
EXPORT_PATH = '/home/ubuntu/af-env/data/stats/'


def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path


def get_account_stats(uid, date_str):
    daily_stats = mg.daily_stats.find_one({"_id": "%s-%s" % (uid, date_str)}) or {}
    daily_recharge = daily_stats['recharge']['total'] if 'recharge' in daily_stats else 0
    daily_win = daily_stats['win']['total'] if 'win' in daily_stats else 0
    user_stats = redis_cache.get_user_stats(uid)
    total_recharge = int(user_stats.get('total_recharge', 0))
    total_win = int(user_stats.get('total_win', 0))
    return daily_recharge, daily_win, total_recharge, total_win


cmd = sys.argv[1]
if cmd == 'stats':
    days_ago = int(sys.argv[2])
    now = datetime.datetime.now() 
    start_date = now - datetime.timedelta(days=days_ago)
    start_date = start_date.replace(hour=16, minute=0, second=0, microsecond=0)
    end_date = now - datetime.timedelta(days=days_ago-1)
    end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
    items = DoubleRechargeCampaign.query.filter(DoubleRechargeCampaign.created_at > start_date).filter(
        DoubleRechargeCampaign.created_at < end_date).all()
    r_list = []
    for item in items:
        user_id = item.user_id
        if not items.coupons:
            continue
        coupon_id = int(item.coupons.split(',')[0])
        coupon = AccountCoupon.query.filter(AccountCoupon.id == coupon_id).first()
        coupon_used = True if coupon.status == 2 else False
        daily_recharge, daily_win, total_recharge, total_win = get_account_stats(user_id, tz.utc_to_local(item.created_at).strftime('%Y-%m-%d'))
        r_list.append((user_id, item.level, item.current_price, True if item.is_double else False, coupon_used,
            daily_recharge, total_recharge, tz.utc_to_local_str(item.created_at)))
    excel_header = [u'uid', u'奖励等级', u'本次充值金额', u'奖励翻倍', u'红包是否使用', u'当天充值金额', u'总充值金额', u'充值时间']
    file_path = redirect_to_file(r_list, excel_header, u'double_recharge_data_%s.xlsx' % end_date.strftime('%y-%m-%d'))
    mail_sender.send(u"[%s]充500送500活动" % end_date.strftime('%y-%m-%d'), u'详情请见附件', attachments=[file_path])
if cmd == 'box':
    from luckycommon.campaign.model.box_recharge_campaign import *
    items = BoxRecord.query.filter(BoxRecord.campaign_id==60011).all()
    r_list = []
    for item in items:
        user_id = item.user_id
        consume_price = item.consume_price
        coupon_id = int(item.coupons.split(',')[0])
        coupon = AccountCoupon.query.filter(AccountCoupon.id == coupon_id).first()
        coupon_used = True if coupon.status == 2 else False
        coupon_price = coupon.price
        daily_recharge, daily_win, total_recharge, total_win = get_account_stats(user_id, tz.utc_to_local(item.created_at).strftime('%Y-%m-%d'))
        r_list.append((user_id, consume_price, coupon_price, coupon_used, daily_recharge, total_recharge, tz.utc_to_local_str(item.created_at)))
    excel_header = [u'uid', u'消耗钻石', u'获取红包金额', u'红包是否使用', u'当天充值金额', u'总充值金额', u'领取时间']
    file_path = redirect_to_file(r_list, excel_header, u'double_recharge_data_60011.xlsx')
    mail_sender.send(u"[60011]宝箱充值活动", u'详情请见附件', attachments=[file_path])
if cmd == 'new':
    from luckycommon.model.campaign import *
    items = NewRechargeCampaign.query.filter(NewRechargeCampaign.campaign_id==50013).all()
    r_list = []
    for item in items:
        uid = item.user_id
        level = item.level
        current_price = item.current_price
        status = item.status
        if status > 0:
            coupons = item.coupons.split(',')
            is_double = True if len(coupons) > 1 else False
            coupon_id = coupons[0]
            coupon = AccountCoupon.query.filter(AccountCoupon.id == coupon_id).first()
            coupon_used = True if coupon.status == 2 else False
            coupon_price = coupon.price
        else:
            coupon_used = False
            coupon_price = None
        daily_recharge, daily_win, total_recharge, total_win = get_account_stats(uid, tz.utc_to_local(item.created_at).strftime('%Y-%m-%d'))
        r_list.append((uid, level, is_double, current_price, status, coupon_used, coupon_price, daily_recharge, total_recharge,
            tz.utc_to_local_str(item.created_at), tz.utc_to_local_str(item.updated_at)))
    excel_header = [u'uid', u'奖励等级', u'奖励翻倍', u'本次充值额度', u'红包是否领取', u'红包是否使用',
        u'红包金额', u'当天充值金额', u'总充值金额', u'产生时间', u'领取时间']
    file_path = redirect_to_file(r_list, excel_header, u'new_recharge_data_50013.xlsx')
    mail_sender.send(u"[50013]翻倍充值活动", u'详情请见附件', attachments=[file_path])
