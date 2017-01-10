# -*- coding:utf-8 -*-
from __future__ import absolute_import
import os
import re
import sys
from datetime import datetime, timedelta

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache

from luckycommon.account.model.account import Account, AccountThird
from luckycommon.model.strategy import StrategyPrivilege, PRIVILEGE_TYPE
from luckycommon.db.activity import get_activity
from luckycommon.stats import MG as mg
from luckycommon.utils.tz import local_now
from luckycommon.utils.mail import MailSender


mail_sender = MailSender.getInstance()
mail_sender.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@zhuohan-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@zhuohan-tech.com>',
    'to': ['wangshanshan@zhuohan-tech.com',
           'wangfeng@zhuohan-tech.com',
           'shuxiang@zhuohan-tech.com']
})


def get_account_stats(uid):
    daily_stats = mg.daily_stats.find_one({"_id": "%s-%s" % ( 
        uid, (local_now() - timedelta(1)).strftime('%Y-%m-%d'))}) or {}
    daily_recharge = daily_stats['recharge']['total'] if 'recharge' in daily_stats else 0
    daily_win = daily_stats['win']['total'] if 'win' in daily_stats else 0
    user_stats = redis_cache.get_user_stats(uid)
    total_recharge = int(user_stats.get('total_recharge', 0))
    total_win = int(user_stats.get('total_win', 0))
    return daily_recharge, daily_win, total_recharge, total_win


COM=re.compile('INFO (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d),\d+ check result (.+), winner:(\d+), need_virtual:(.+?), is_virtual:(.+?), need_loser:(.+?), is_loser:(.+?), need_adjust:(.+?), adjust_reason:(.+)')
FAIL_COM = re.compile('INFO (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d),\d+ adjust result fail, left delta:(\d+), target_amount:(\d+)')
FREE_COM = re.compile('INFO (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d),\d+ strategy daily free add uid:(\d+),aid:(.+),amount:(\d+)')
RATIO_COM = re.compile('INFO (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d),\d+ standard_reached check ratio fail, uid:(\d+), aid:(.+)')
v_adjust_list = []
loser_adjust_list = []
fail_adjust_list = []
free_list = []
ratio_dict = dict()

fd = open('/var/log/lucky/worker.log.1','r')
for line in fd:
    line = line.strip()
    match = COM.match(line)
    if match:
        announce_time = match.group(1)
        activity_id = match.group(2)
        winner_id = match.group(3)
        need_virtual = match.group(4)
        is_virtual = match.group(5)
        need_loser = match.group(6)
        is_loser = match.group(7)
        need_adjust = match.group(8)
        adjust_reason = match.group(9)
        if is_virtual == 'False' and need_loser == 'False' and need_adjust == 'True':
            print 'found adjust, %s, winner:%s, timer:%s' % (activity_id, winner_id, announce_time)
            v_adjust_list.append({'activity_id': activity_id, 'winner_id': winner_id, 'time': announce_time, 'reason': adjust_reason})
        if need_loser == 'True' and need_adjust == 'True':
            loser_adjust_list.append({'activity_id': activity_id, 'winner_id': winner_id, 'time': announce_time, 'reason': adjust_reason})
    fail_match = FAIL_COM.match(line)
    if fail_match:
        adjust_time = fail_match.group(1)
        left_delta = fail_match.group(2)
        target_amount = fail_match.group(3)
        fail_adjust_list.append({'time': adjust_time, 'left_delta': left_delta, 'target_amount': target_amount})
    free_match = FREE_COM.match(line)
    if free_match:
        adjust_time = free_match.group(1)
        uid = free_match.group(2)
        aid = free_match.group(3)
        amount = free_match.group(4)
        free_list.append({'time': adjust_time, 'uid': uid, 'aid': aid, 'amount': amount})
    ratio_match = RATIO_COM.match(line)
    if ratio_match:
        adjust_time = ratio_match.group(1)
        uid = ratio_match.group(2)
        aid = ratio_match.group(3)
        ratio_dict[aid] = {'time': adjust_time, 'uid': uid}

html_str = '<html><head></head><body>'
html_str += u'<h1>调整失败列表</h1><br />'
for item in fail_adjust_list:
    time = item['time']
    left_delta = item['left_delta']
    target_amount = item['target_amount']
    html_str += u'调整时间:%s, 活动价格:%s, 剩余调整数字:%s <br />' % (time, target_amount, left_delta)

html_str += u'<h1>调整列表(真实->虚拟)</h1><br />'
for item in v_adjust_list: 
    activity_id = item['activity_id']
    winner_id = item['winner_id']
    time = item['time']
    reason = item['reason'].decode('utf-8')
    activity = get_activity(activity_id)
    html_str += u'调整时间:%s, 调整原因:%s, 中奖者编号:%s, 活动编号:%s(http://www.1yuan-gou.com/activity/%s), 活动期数:%s, 活动名称:%s <br />' % (
        time, reason, winner_id, activity.template_id, activity_id, activity.term_number, activity.name)


html_str += '<hr>'
html_str += u'<h1>调整列表(真实/虚拟->输家)</h1><br />'
for item in loser_adjust_list:
    activity_id = item['activity_id']
    winner_id = item['winner_id']
    time = item['time']
    activity = get_activity(activity_id)
    html_str += u'调整时间:%s, 中奖者编号:%s, 活动编号:%s(http://www.1yuan-gou.com/activity/%s), 活动期数:%s, 活动名称:%s <br />' % (
        time, winner_id, activity.template_id, activity_id, activity.term_number, activity.name)


html_str += u'<h1>放开列表</h1><br />'
for item in free_list:
    activity_id = item['aid']
    uid = item['uid']
    time = item['time']
    amount = item['amount']
    daily_recharge, daily_win, total_recharge, total_win = get_account_stats(uid)
    html_str += u'时间:%s, 中奖者编号:%s, 放开中奖额度:%s, 活动链接http://www.1yuan-gou.com/activity/%s , 当日充值:%s, 当日中奖:%s, 累积充值:%s, 累积中奖:%s<br />' % (
        time, uid, amount, activity_id, daily_recharge, daily_win, total_recharge, total_win)

html_str += '<hr>'
html_str += u'<h1>A+特权</h1><br />'
aplus_list = []
now = datetime.now()
start_date = now - timedelta(days=1)
start_date = start_date.replace(hour=16, minute=0, second=0, microsecond=0)
end_date = now.replace(hour=16, minute=0, second=0, microsecond=0)
items = StrategyPrivilege.query.filter(StrategyPrivilege.updated_at > start_date.strftime('%Y-%m-%d %H:%M:%S'))\
                               .filter(StrategyPrivilege.updated_at < end_date.strftime('%Y-%m-%d %H:%M:%S')).all()
for item in items:
    privilege_type = item.privilege_type
    uid = item.user_id
    if privilege_type == 0 and item.used:
        daily_recharge, daily_win, total_recharge, total_win = get_account_stats(uid)
        used_time = item.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        html_str += u'使用时间:%s, uid:%s, 当日充值:%s, 当日中奖:%s, 累积充值:%s, 累积中奖:%s<br />' % (
            used_time, uid, daily_recharge, daily_win, total_recharge, total_win)


html_str += '<hr>'
html_str += u'<h1>赢家概率阻挡</h1><br />'
for k,v in ratio_dict.items():
    aid = k
    uid = v['uid']
    time = v['time']
    html_str += u'阻挡时间:%s, uid:%s, 活动链接:http://www.1yuan-gou.com/activity/%s<br />' % (time, uid, aid)
    
html_str += '</body></html>'
#print html_str
mail_sender.send("昨日调整清单", html_str)
