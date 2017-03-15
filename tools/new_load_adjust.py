# -*- coding:utf-8 -*-
from __future__ import absolute_import
import os
import re
import sys
import tablib
from datetime import datetime, timedelta

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache

from luckycommon.model.pay import Pay
from luckycommon.db import activity as activity_db
from luckycommon.stats import MG as mg
from luckycommon.utils import tz
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

EXPORT_PATH = '/home/ubuntu/af-env/data/stats/'


def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path

COM=re.compile('INFO (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d),\d+ check result (.+), winner:(\d+), need_virtual:(.+?), is_virtual:(.+?), need_loser:(.+?), is_loser:(.+?), need_adjust:(.+?), adjust_reason:(.+)')
FREE_COM = re.compile('INFO (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d),\d+ strategy daily free add uid:(\d+),aid:(.+),amount:(\d+)')
RATIO_COM = re.compile('INFO (\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d),\d+ standard_reached check ratio fail, uid:(\d+), aid:(.+)')


def parse_log():
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
	    final_winner = activity_db.get_winner_id(activity_id)
	    activity = activity_db.get_activity(activity_id)
	    if need_adjust == 'True':
		adjust_succ = False if final_winner == int(winner_id) else True
		data = {
		    'activity_id': activity_id,
		    'name': activity.short_title or activity.name,
		    'gid': activity.template_id,
		    'target_amount': activity.target_amount,
		    'term_number': activity.term_number,
		    'announce_time': announce_time,
		    'origin_winner': winner_id,
		    'final_winner': final_winner,
		    'adjust_succ': adjust_succ,
		    'adjust_reason': adjust_reason,
		}
		virtual_win = redis_cache.is_virtual_account(final_winner)
		data.update({'virtual_win': virtual_win})
		after_recharge = 0
		if not virtual_win:
		    items = Pay.query.filter(Pay.user_id == final_winner).filter(Pay.status == 2).filter(Pay.created_at > announce_time).all()
		    for item in items:
			after_recharge += item.price
		data.update({'after_recharge': float(after_recharge)})
		mg.strategy_stats.save(data)
	ratio_match = RATIO_COM.match(line)
	if ratio_match:
	    adjust_time = ratio_match.group(1)
	    uid = ratio_match.group(2)
	    aid = ratio_match.group(3)
	    stats = mg.strategy_stats.find_one({'activity_id': aid})
	    if stats:
		mg.strategy_stats.update({'activity_id': aid}, {'$set': {'adjust_reason': u'赢家概率阻挡'}})
	free_match = FREE_COM.match(line)
	if free_match:
	    adjust_time = free_match.group(1)
	    uid = free_match.group(2)
	    aid = free_match.group(3)
	    amount = free_match.group(4)
	    stats = mg.strategy_stats.find_one({'activity_id': aid})
	    if not stats:
		activity = activity_db.get_activity(aid)
		final_winner = activity_db.get_winner_id(aid)
		data = {
		    'activity_id': aid,
		    'name': activity.short_title or activity.name,
		    'gid': activity.template_id,
		    'target_amount': activity.target_amount,
		    'term_number': activity.term_number,
		    'announce_time': adjust_time,
		    'origin_winner': final_winner,
		    'final_winner': final_winner,
		    'adjust_succ': 0,
		    'adjust_reason': u'放开策略',
		}
		virtual_win = redis_cache.is_virtual_account(final_winner)
		data.update({'virtual_win': virtual_win})
		after_recharge = 0
		if not virtual_win:
		    items = Pay.query.filter(Pay.user_id == final_winner).filter(Pay.status == 2).filter(Pay.created_at > adjust_time).all()
		    for item in items:
			after_recharge += item.price
		data.update({'after_recharge': float(after_recharge)})
		mg.strategy_stats.save(data)


def send_mail(days_ago=1):
    now = datetime.now()
    start_date = (now-timedelta(days_ago)).replace(hour=16,minute=0,second=0)
    end_date = (now-timedelta(days_ago-1)).replace(hour=16,minute=0,second=0)
    s_list = []
    print start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')
    stats = mg.strategy_stats.find({'announce_time': {'$gt': start_date.strftime('%Y-%m-%d %H:%M:%S'), '$lt': end_date.strftime('%Y-%m-%d %H:%M:%S')}})
    for stat in stats:
	origin_winner_activity = activity_db.get_user_activity(stat['origin_winner'], stat['activity_id'])
	final_winner_activity = activity_db.get_user_activity(stat['final_winner'], stat['activity_id'])
	origin_winner_num_count = len(origin_winner_activity.numbers.split(','))
	final_winner_num_count = len(final_winner_activity.numbers.split(','))
	s_list.append((stat['gid'], stat['activity_id'], stat['name'],
	    stat['term_number'], stat['target_amount'],
	    tz.utc_to_local_str(datetime.strptime(stat['announce_time'], '%Y-%m-%d %H:%M:%S')),
	    '%s(%s)' % (stat['final_winner'], final_winner_num_count), '%s(%s)' % (stat['origin_winner'], origin_winner_num_count), stat['adjust_reason'],
	    stat['adjust_succ'], stat['after_recharge']))
    excel_header = [u'gid', u'aid', u'name', u'term_number', u'目标人次', u'开奖时间', u'中奖者(参与人次)', u'原中奖者(参与人次)', u'调整原因', u'调整成功', u'中奖后充值']
    date_title = tz.utc_to_local(start_date).strftime('%Y-%m-%d')
    file_path = redirect_to_file(s_list, excel_header, u'adjust_table_%s.xlsx' % date_title)
    mail_sender.send(u'[%s]调整清单beta1.1' % date_title, u'详情请见附件', attachments=[file_path])


if __name__ == "__main__":
    parse_log()
    send_mail()
