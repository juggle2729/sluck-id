# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import time
import tablib
import datetime
import logging

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckyapi.logic.coupon import send_coupon_to_user
from luckycommon.model.coupon import AccountCoupon
from luckycommon.db.account import get_account
from luckycommon.cache import redis_cache
from luckycommon.stats import MG as mg
from luckycommon.utils.tz import utc_to_local
from luckycommon.utils import id_generator
from luckycommon.utils import tz
from luckycommon.utils.mail import MailSender
from luckycommon.third.sms.helper import send_sms


COUPON_TID = 220
SMS_ID = 'scuaE'
START_DT = datetime.datetime.strptime('2016-04-30 16:00:00', '%Y-%m-%d %H:%M:%S')
VALID_DT = datetime.datetime.strptime('2016-06-23 4:00:00', '%Y-%m-%d %H:%M:%S')
_LOGGER = logging.getLogger('worker')

BOSS_UIDS = [15012460, 15142423, 15041625]
mail_sender = MailSender.getInstance()
mail_sender.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@zhuohan-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@zhuohan-tech.com>',
    'to': [
           'wangshanshan@zhuohan-tech.com',
           'wangfeng@zhuohan-tech.com',
           'shuxiang@zhuohan-tech.com',
           'jiangyan@zhuohan-tech.com'
    ]
    #'to': ['shuxiang@zhuohan-tech.com']
})
EXPORT_PATH = '/home/ubuntu/af-env/data/stats/'


def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path


def get_card_user():
    """
    获取玩过淘宝购物卡的用户
    """
    from luckycommon.db.activity import get_activity_users
    user_s = set()
    for term in xrange(1000, 20000):
        aid = id_generator.generate_uuid(
            'activity:%s:%s' % (462, term))
        ua_items = get_activity_users(aid)
        for ua in ua_items:
            uid = ua.user_id
	    user_stats = mg.user_stats.find_one({'_id': uid})
            if not user_stats:
                continue
            #print uid
            last_active_at = user_stats['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
	    total_recharge = int(user_stats['recharge'].get('total', 0)) if 'recharge' in user_stats else 0
            if total_recharge > 500:
                if last_active_at < '2016-08-15 16:00:00':
                    user_s.add(uid) 
                    print uid, total_recharge, last_active_at
    user_stats = mg.user_stats.find({'_id': {'$in': list(user_s)}})
    return user_stats, 'sms_notify_e', 'Z5yCQ', u'玩过微信红包用户'


def get_account_stats(uid, dt):
    daily_stats = mg.daily_stats.find_one({"_id": "%s-%s" % ( 
        uid, dt.strftime('%Y-%m-%d'))}) or {}
    daily_recharge = daily_stats['recharge'].get('total', 0) if 'recharge' in daily_stats else 0
    daily_win = daily_stats['win']['total'] if 'win' in daily_stats else 0
    user_stats = mg.user_stats.find_one({'_id': uid})
    total_recharge = int(user_stats['recharge'].get('total', 0)) if 'recharge' in user_stats else 0
    print uid, total_recharge
    total_win = int(user_stats['win'].get('total', 0)) if 'win' in user_stats else 0
    last_active_at = user_stats['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
    return daily_recharge, daily_win, total_recharge, total_win, last_active_at


TARGET_CHNS = ['lic01','lic04','lic06','yingyongbao','jiangy03','jiangy05','huawei,oppo','vivo','baidux1','mm02','mm03','mm04']


def get_user_stats_A():
    """
    5.1-5.15期间注册未付费用户
    """
    start_dt = datetime.datetime.strptime('2016-04-30 16:00:00', '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.datetime.strptime('2016-05-14 16:00:00', '%Y-%m-%d %H:%M:%S')
    #user_stats = mg.user_stats.find({'pay.count': {'$gt': 10}, 'updated_at': {'$gt': start_dt, '$lt': end_dt}})
    user_stats = mg.user_stats.find({'$or': [{'recharge': {'$exists': 0}, 'chn': {'$in': TARGET_CHNS}, 'created_at': {'$gt': start_dt, '$lt': end_dt}}, {'_id': {'$in': BOSS_UIDS}}]})
    return user_stats, 'sms_notify_a', 'VdJ2N4', u'5.1-5.15期间注册未付费用户'


def get_user_stats_B():
    """
    4.15-4.30期间注册未付费用户 
    """
    start_dt = datetime.datetime.strptime('2016-04-14 16:00:00', '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.datetime.strptime('2016-04-29 16:00:00', '%Y-%m-%d %H:%M:%S')
    user_stats = mg.user_stats.find({'$or': [{'recharge': {'$exists': 0}, 'chn': {'$in': TARGET_CHNS}, 'created_at': {'$gt': start_dt, '$lt': end_dt}}, {'_id': {'$in': BOSS_UIDS}}]})
    return user_stats, 'sms_notify_b', '4Vm893', u'4.15-4.30期间注册未付费用户'


def get_user_stats_C():
    """
    4.1-4.30期间激活未注册（安卓）用户
    """
    start_dt = datetime.datetime.strptime('2016-03-31 16:00:00', '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.datetime.strptime('2016-04-14 16:00:00', '%Y-%m-%d %H:%M:%S')
    user_stats = mg.user_stats.find({'$or': [{'recharge': {'$exists': 0}, 'chn': {'$in': TARGET_CHNS}, 'created_at': {'$gt': start_dt, '$lt': end_dt}}, {'_id': {'$in': BOSS_UIDS}}]})
    return user_stats, 'sms_notify_c', 'AF3ab1', u'4.1-4.30期间激活未注册（安卓）用户'


def get_user_stats_D():
    """
    4月份有付费行为
    """
    start_dt = datetime.datetime.strptime('2016-03-31 16:00:00', '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.datetime.strptime('2016-04-30 16:00:00', '%Y-%m-%d %H:%M:%S')
    user_stats = mg.user_stats.find({'recharge.total': {'$gt': 0}, 'updated_at': {'$gt': start_dt, '$lt': end_dt}})
    return user_stats, 'sms_notify_d', 'scuaE', u'4月份有付费行为'


def get_user_stats_test():
    """
    测试
    """
    user_stats = mg.user_stats.find({'_id': {'$in':[15041625]}})
    return user_stats, 'sms_notify_e', 'Z5yCQ', u'玩过微信红包用户'


cmd = sys.argv[1]
if cmd == 'start':
    index = sys.argv[2]
    if 'a' == index:
        user_stats, sms_template, sms_id, sms_desc = get_user_stats_A()
    elif 'b' == index:
        user_stats, sms_template, sms_id, sms_desc = get_user_stats_B()
    elif 'c' == index:
        user_stats, sms_template, sms_id, sms_desc = get_user_stats_C()
    elif 'd' == index:
        user_stats, sms_template, sms_id, sms_desc = get_user_stats_D()
    elif 'e' == index:
        user_stats, sms_template, sms_id, sms_desc = get_card_user()
    elif 'test' == index:
        user_stats, sms_template, sms_id, sms_desc = get_user_stats_test()
    else:
        sys.exit()
    #l = [x for x in user_stats]
    #print len(l)
    #sys.exit()
    count = 0
    for user in user_stats:
        uid = user['_id']
        chn = user.get('chn')
        updated_at = user['updated_at']
        sms_item = mg.sms_stats.find_one({'uid': uid, 'sms_id': sms_id})
        if sms_item:
            continue
        if chn in ['ios', 'ios_pro', 'ios_hd', 'qg_ios', 'qg_pro', 'qg_hd']:
            link = 'http://dwz.cn/2ONHHn'
        else:
            link = 'http://t.cn/R5OYmZE' # select by chn
        params = {
            "link": link,
        }
        account = get_account(uid)
        if account.is_virtual == 1 or account.status == 1:
            continue
        try:
            dt = tz.local_now() - datetime.timedelta(0)
            daily_recharge, daily_win, total_recharge, total_win, last_active_at = get_account_stats(int(uid), dt)
            data = {
                'uid': uid,
                'sms_id': sms_id,
                'chn': chn,
                'sms_desc': sms_desc,
                'before_total_recharge': total_recharge,
                'before_total_win': total_win,
                'before_active_at': updated_at
            }
            mg.sms_stats.save(data)
            send_sms([account.phone], sms_template, params)
            _LOGGER.info('send campaign sms to %s', uid)
            #send_coupon_to_user(uid, COUPON_TID, 1, coupon_from=u'短信召回')
            count += 1
        except Exception as e:
            _LOGGER.error('send campaign sms to %s error %s', uid, e)
    _LOGGER.info('total send campaign sms %s', count)


if cmd == 'load':
    sms_id = sys.argv[2]
    sms_list = []
    stats_items = mg.sms_stats.find({'sms_id': sms_id})
    for item in stats_items:
        uid = item['uid']
        dt = tz.local_now() - datetime.timedelta(0)
        daily_recharge, daily_win, total_recharge, total_win, last_active_at = get_account_stats(int(uid), dt)
        #coupon = AccountCoupon.query.filter(AccountCoupon.user_id == uid).filter(AccountCoupon.template_id == COUPON_TID).first()
        #coupon_used = True if coupon.status == 2 else False
        data = {
            'after_active_at': last_active_at,
            'daily_recharge': daily_recharge,
            'daily_win': daily_win,
            'after_total_recharge': total_recharge,
            'after_total_win': total_win,
            #'coupon_used': coupon_used,
            'updated_at': dt.strftime('%Y-%m-%d %H:%M:%S')
        }
        mg.sms_stats.update({'uid': uid, 'sms_id': sms_id}, {'$set': data}, upsert=True)
        sms_list.append((
            uid, sms_id, item.get('sms_desc'), item.get('chn'), item.get('before_active_at'), last_active_at,
            item.get('before_total_recharge', 0), total_recharge
        ))
    excel_header = [u'uid', u'sms_id', u'sms_desc', u'chn', u'召回前活跃时间', u'召回后活跃时间', u'召回前充值', u'召回后充值']
    file_path = redirect_to_file(sms_list, excel_header, u'sms_callback_data_%s.xlsx' % sms_id)
    mail_sender.send(u"[%s]短信召回数据" % sms_id, u'详情请见附件', attachments=[file_path])
if cmd == 'card':
    get_card_user()
