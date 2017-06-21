# -*- coding: utf-8 -*-
from __future__ import absolute_import

import datetime
import os
import sys
from sets import Set

# add up one level dir into sys path

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache

from luckycommon.account.internal_handler import get_account
from luckycommon.model.mission import FreshMission
from luckycommon.model.campaign import (NewRechargeCampaign, RechargeCampaign)
from luckycommon.campaign.model.fortune_wheel import FortuneWheel, FortuneWheelAward, AWARD_RATIO
from luckycommon.campaign.model.miss_return import *
from luckycommon.campaign.model.first_double import *
from luckycommon.stats import MG as mg
from luckycommon.utils import tz
from luckycommon.utils.orm import get_count
from luckycommon.utils.mail import TOOL_MAIL_SENDER


def get_account_stats(uid, date_str):
    daily_stats = mg.daily_stats.find_one({"_id": "%s-%s" % (uid, date_str)}) or {}
    daily_recharge = daily_stats['recharge']['total'] if 'recharge' in daily_stats else 0
    daily_win = daily_stats['win']['total'] if 'win' in daily_stats else 0
    user_stats = redis_cache.get_user_stats(uid)
    total_recharge = int(user_stats.get('total_recharge', 0))
    total_win = int(user_stats.get('total_win', 0))
    return daily_recharge, daily_win, total_recharge, total_win


def calc_wheel(html):
    now = datetime.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    start_date = now - datetime.timedelta(days=1)
    items = FortuneWheel.query.filter(FortuneWheel.date == date_str).all()
    total_apply = 0
    total_left = 0
    total_person = 0
    new_apply = 0
    new_left = 0
    new_person = 0
    play_dict = {}
    new_play_dict = {}
    for item in items:
        uid = item.user_id
        apply_times = item.apply_times
        left_times = item.left_times
        total_apply += apply_times
        total_left += left_times
        if apply_times > 0:
            total_person += 1
        play_dict.setdefault(apply_times, 0)
        play_dict[apply_times] += 1
        account = get_account(uid)
        if account.created_at.strftime('%Y-%m-%d %H:%M:%S') > start_date.strftime('%Y-%m-%d %H:%M:%S'):
            new_apply += apply_times
            new_left += left_times
            if apply_times > 0:
                new_person += 1
        new_play_dict.setdefault(apply_times, 0)
        new_play_dict[apply_times] += 1
    play_list = [(k, v) for k, v in play_dict.items()]
    play_list.sort(key=lambda x: x[0], reverse=True)
    new_play_list = [(k, v) for k, v in new_play_dict.items()]
    new_play_list.sort(key=lambda x: x[0], reverse=True)
    award_dict = {}
    items = FortuneWheelAward.query.filter(FortuneWheelAward.date == date_str).all()
    for item in items:
        award_index = item.award_index
        award_dict.setdefault(award_index, 0)
        award_dict[award_index] += 1
    award_list = [(k, AWARD_RATIO[k]['name'], v) for k, v in award_dict.items()]
    award_list.sort(key=lambda x: x[2], reverse=True)
    html += u'<h2>每日转盘抽奖</h2>'
    html += u'今日转盘总人数:%s<br />' % total_person
    html += u'今日转盘总次数:%s<br />' % total_apply
    html += u'今日转盘新用户总人数:%s<br />' % new_person
    html += u'今日转盘新用户总次数:%s<br />' % new_apply
    html += u'参与次数统计<br />'
    for p in play_list:
        html += u'参与%s次人数:%s<br />' % (p[0], p[1])
    html += u'新用户参与次数统计<br />'
    for p in new_play_list:
        html += u'参与%s次人数:%s<br />' % (p[0], p[1])
    html += u'中奖商品统计<br />'
    for a in award_list:
        html += u'中奖商品:%s 中奖次数:%s<br />' % (a[1], a[2])

    return html


cmd = sys.argv[1]
if cmd == 'stats':
    days_ago = int(sys.argv[2])
    start_date = tz.local_now() - datetime.timedelta(days=days_ago)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + datetime.timedelta(days=1)
    active_users = mg.daily_stats.find({"updated_at": {"$lt": end_date, "$gte": start_date}})
    active_user_count = mg.daily_stats.find({"updated_at": {"$lt": end_date, "$gte": start_date}}).count()
    active_user_set = Set()
    for item in active_users:
        active_user_set.add(int(item['user_id']))
    # first double campaign
    print 'check first double from %s' % tz.local_to_utc_str(start_date)
    apply_query = FirstDouble.query.filter(FirstDouble.created_at > tz.local_to_utc_str(start_date)).filter(
        FirstDouble.created_at < tz.local_to_utc_str(end_date))
    firstdouble_apply_count = get_count(apply_query)
    used_query = apply_query.filter(FirstDouble.status == 2)
    firstdouble_used_count = get_count(used_query)
    print 'firstdouble', firstdouble_apply_count, firstdouble_used_count
    items = used_query.all()
    all_user_attend_firstdouble_query = FirstDouble.query.filter()
    all_user_attend_firstdouble_count = get_count(all_user_attend_firstdouble_query)
    all_user_attend_firstdouble_items = all_user_attend_firstdouble_query.all()
    all_user_attend_firstdouble_set = Set()
    for item in all_user_attend_firstdouble_items:
        all_user_attend_firstdouble_set.add(int(item.user_id))

    active_attend_firstdouble_set = active_user_set.intersection(all_user_attend_firstdouble_set)
    active_attend_firstdouble_count = len(active_attend_firstdouble_set)
    firstdouble_recharge_amount = 0
    firstdouble_daily_recharge = 0
    firstdouble_fresh_recharge_amount = 0
    firstdouble_fresh_daily_recharge = 0
    firstdouble_fresh_used_count = 0
    firstdouble_fresh_apply_count = 0
    for item in apply_query.all():
        uid = item.user_id
        account = get_account(uid)
        if account.created_at.strftime('%Y-%m-%d %H:%M:%S') > tz.local_to_utc_str(start_date):
            firstdouble_fresh_apply_count += 1

    for item in items:
        uid = item.user_id
        daily_recharge, daily_win, total_recharge, total_win = get_account_stats(uid, start_date.strftime('%Y-%m-%d'))
        firstdouble_recharge_amount += item.recharge_price
        firstdouble_daily_recharge += daily_recharge
        account = get_account(uid)
        if account.created_at.strftime('%Y-%m-%d %H:%M:%S') > tz.local_to_utc_str(start_date):
            firstdouble_fresh_recharge_amount += item.recharge_price
            firstdouble_fresh_daily_recharge += daily_recharge
            firstdouble_fresh_used_count += 1
    # miss return campaign
    print 'check miss return from %s' % tz.local_to_utc_str(start_date)
    return_query = MissReturn.query.filter(MissReturn.created_at > tz.local_to_utc_str(start_date)).filter(
        MissReturn.created_at < tz.local_to_utc_str(end_date))
    return_count = get_count(return_query)
    return_items = return_query.all()
    all_user_attend_return_query = MissReturn.query.filter()
    all_user_attend_return_count = get_count(all_user_attend_return_query)
    all_user_attend_return_items = all_user_attend_return_query.all()
    all_user_attend_return_set = Set()
    for item in all_user_attend_return_items:
        all_user_attend_return_set.add(int(item.user_id))

    active_attend_return_set = active_user_set.intersection(all_user_attend_return_set)
    active_attend_return_count = len(active_attend_return_set)
    print 'miss return size: %s' % return_count
    return_fresh_count = 0
    return_amount = 0
    return_daily_recharge = 0
    return_fresh_amount = 0
    return_fresh_daily_recharge = 0
    for item in return_items:
        uid = item.user_id
        daily_recharge, daily_win, total_recharge, total_win = get_account_stats(uid, start_date.strftime('%Y-%m-%d'))
        return_daily_recharge += daily_recharge
        return_amount += item.consume_amount
        account = get_account(uid)
        if account.created_at.strftime('%Y-%m-%d %H:%M:%S') > tz.local_to_utc_str(start_date):
            return_fresh_count += 1
            return_fresh_daily_recharge += daily_recharge
            return_fresh_amount += item.consume_amount
    # fresh mission
    print 'check fresh mission'
    total_fresh_count = get_count(FreshMission.query.filter(FreshMission.status == 1))
    new_fresh_count = get_count(
        FreshMission.query.filter(FreshMission.updated_at > tz.local_to_utc_str(start_date)).filter(
            FreshMission.status == 1))
    # recharge campaign
    recharge_query = RechargeCampaign.query.filter(
        RechargeCampaign.created_at > tz.local_to_utc_str(start_date)).filter(RechargeCampaign.level > 0)
    recharge_count = get_count(recharge_query)
    recharge_award_count = get_count(recharge_query.filter(RechargeCampaign.status > 0))
    # new recharge campaign
    recharge_query = NewRechargeCampaign.query.filter(
        NewRechargeCampaign.created_at > tz.local_to_utc_str(start_date))
    new_recharge_count = get_count(recharge_query)
    new_recharge_award_count = get_count(recharge_query.filter(NewRechargeCampaign.status > 0))
    html = '<html><body>'
    html += u'<h2>今日活跃用户人数:%s</h2>' % active_user_count
    html += u'<h2>今日活跃用户中所有参加不中包赔的用户数:%s</h2>' % active_attend_return_count
    html += u'<h2>今日活跃用户中今日参加不中包赔的用户数:%s</h2>' % return_count
    html += u'<h2>今日活跃用户中以前参加不中包赔的用户数:%s</h2>' % (active_attend_return_count - return_count)
    html += u'<h2>不中包赔活动-今日新用户完成:%s</h2>' % return_fresh_count
    html += u'<h2>不中包赔活动-今日返还红包额度:%s</h2>' % return_amount
    html += u'<h2>不中包赔活动-今日参与用户充值额度:%s</h2>' % return_daily_recharge
    html += u'<h2>不中包赔活动-今日返还新用户红包额度:%s</h2>' % return_fresh_amount
    html += u'<h2>不中包赔活动-今日参与新用户充值额度:%s</h2>' % return_fresh_daily_recharge

    html += u'<h2>今日活跃用户中所有参加首充翻倍(报名)的用户数:%s</h2>' % active_attend_firstdouble_count
    html += u'<h2>今日活跃用户中今日参加首充翻倍(报名)的用户数:%s</h2>' % firstdouble_apply_count
    html += u'<h2>今日活跃用户中以前参加首充翻倍(报名)的用户数:%s</h2>' % (active_attend_firstdouble_count - firstdouble_apply_count)
    html += u'<h2>首充翻倍活动-今日报名并完成:%s</h2>' % firstdouble_used_count
    html += u'<h2>首充翻倍活动-今日参与用户活动内充值额度:%s</h2>' % firstdouble_recharge_amount
    html += u'<h2>首充翻倍活动-今日参与用户充值额度:%s</h2>' % firstdouble_daily_recharge
    html += u'<h2>首充翻倍活动-今日新用户报名:%s</h2>' % firstdouble_fresh_apply_count
    html += u'<h2>首充翻倍活动-今日新用户报名并完成:%s</h2>' % firstdouble_fresh_used_count
    html += u'<h2>首充翻倍活动-今日参与新用户活动内充值额度:%s</h2>' % firstdouble_fresh_recharge_amount
    html += u'<h2>首充翻倍活动-今日参与新用户充值额度:%s</h2>' % firstdouble_fresh_daily_recharge
    html += u'<h2>累积充值活动-今日完成:%s</h2>' % recharge_count
    html += u'<h2>累积充值活动-今日领取:%s</h2>' % recharge_award_count
    html += u'<h2>单笔充值活动-今日完成:%s</h2>' % new_recharge_count
    html += u'<h2>单笔充值活动-今日领取:%s</h2>' % new_recharge_award_count
    html += u'<h2>新手任务-累积完成:%s</h2>' % total_fresh_count
    html += u'<h2>新手任务-今日完成:%s</h2>' % new_fresh_count
    html = calc_wheel(html)
    html += '</body></html>'
    # print html
    TOOL_MAIL_SENDER.send("[%s]今日活动数据" % start_date.strftime('%Y-%m-%d'), html)
