# -*- coding: utf-8 -*-
import json
import logging

from django.conf import settings
from luckycommon.account.db import account as account_db
from luckycommon.cache import redis_cache
from luckycommon.campaign.db import miss_return as return_db
from luckycommon.campaign.model.miss_return import *
from luckycommon.credit.db.credit import add_miss_return_credit
from luckycommon.db import activity as activity_db
from luckycommon.utils.tz import now_ts

_LOGGER = logging.getLogger('worker')


def _get_timeline():
    t_list = []
    scrolling_set = redis_cache.range_missreturn_scrolling()
    now = now_ts()
    for scrolling, ts in scrolling_set:
        params = json.loads(scrolling)
        delta_ts = now - int(params['ts'])
        if delta_ts < 60:
            time_ago = '%s seconds ago'
        elif delta_ts < 3600:
            time_ago = '%s minutes ago' % (delta_ts / 60)
        else:
            time_ago = '%s hours ago' % (delta_ts / 3600)
        t_list.append({
            'time': time_ago,
            'uid': params.get('uid'),
            'nick_name': params.get('nick_name'),
            'award_title': params.get('award_title')
        })
    return t_list


def get_status(user_id):
    """
    获取活动参与状态
    """
    data = {}
    item = return_db.get_status(user_id)
    status = 0 if not item else 1
    total_count = return_db.get_award_count()
    timeline = _get_timeline()
    data.update({
        'status': status,
        'total_count': total_count,
        'timeline': timeline
    })
    return data


def _spread(user_id, award_price=None, is_winner=False):
    account = account_db.get_account(user_id)
    if is_winner:
        # award_title = '10 Lucky Coins'
        award_title = u"10 đồng xu"
    else:
        # award_title = '%s Sure to Win Coupon' % award_price
        award_title = u"%s Bồi thường nếu không trúng Lì xì" % award_price
    ts = now_ts()
    scrolling_dict = {
        'ts': ts,
        'uid': account.id,
        'nick_name': account.nick_name,
        'award_title': award_title
    }
    redis_cache.submit_missreturn_scrolling(json.dumps(scrolling_dict, ensure_ascii=False), ts)


def announce_callback(activity, winner):
    """
    开奖回调
    """
    try:
        activity_id = activity.id
        template_id = activity.template_id
        _LOGGER.info('starting to process miss return campaign')
        if template_id != TEMPLATE_ID:
            _LOGGER.info('template is not miss return template')
            return
        user_activitys = activity_db.get_activity_users(activity_id)
        for ua in user_activitys:
            user_id = ua.user_id
            if user_id == winner:
                _spread(user_id, is_winner=True)
                continue
            consume_amount = len(ua.numbers.split(','))
            if consume_amount > MAX_CONSUME_AMOUNT:
                _LOGGER.warn('miss return, announce callback consume_amount exception, %s', consume_amount)
                continue
            item = return_db.check_return(user_id, activity_id, consume_amount)
            if item:
                add_miss_return_credit(user_id, consume_amount * settings.EXCHANGE_RATIO)
                # _spread(user_id, award_price=consume_amount)
                _LOGGER.info('miss return, activity %s return %s to %s success', activity_id, consume_amount, user_id)
    except Exception as e:
        _LOGGER.exception('miss return, announce_callback exception:%s', e)


def check_complete(user_id):
    item = return_db.get_status(user_id)
    return False if not item else True
