# -*- coding: utf-8 -*-
import random
import logging
from datetime import datetime

from luckycommon.campaign import valid_time

from luckycommon.account.db.account import get_account
from luckycommon.db.activity import get_template
from luckycommon.db.coupon import get_coupon_by_id
from luckycommon.campaign.db import recommend_campaign as campaign_db

from luckycommon.utils import id_generator
from luckycommon.utils import exceptions as err
from luckycommon.utils.tz import utc_to_local_str

from django.conf import settings


_LOGGER = logging.getLogger('lucky')


COUPON_RATIO_LIST = [{
    'start': 1, 'end': 20, 'tid': 139,
},{
    'start': 20, 'end': 55, 'tid': 140,
},{
    'start': 55, 'end': 85, 'tid': 141,
},{
    'start': 85, 'end': 100, 'tid': 142,
}]


RECOMMEND_CONF = {
    'children': {
        'start_time': '2016-05-27 00:00:00',
        'end_time': '2016-06-03 23:59:59',
        'group': [{'gid': 416,},{'gid': 417,},{'gid': 221,},{'gid': 419,},
                 {'gid': 418,},{'gid': 420,},{'gid': 400,},{'gid': 303,},
                 {'gid': 401,},{'gid': 402,},{'gid': 403,},{'gid': 404,},
                 {'gid': 405,},{'gid': 406,},{'gid': 407,},{'gid': 410,},
                 {'gid': 409,},{'gid': 408,},{'gid': 249,},{'gid': 411,},
                 {'gid': 412,},{'gid': 413,},{'gid': 414,},{'gid': 415,}]
    }
}


def _choose_coupon(ratio_list=COUPON_RATIO_LIST, count=1):
    tid_list = []
    for _ in range(count):
        rand_int = random.randint(1, 100)
        for ratio_item in ratio_list:
            if rand_int >= ratio_item['start'] and rand_int <= ratio_item['end']:
                tid_list.append(ratio_item['tid'])
                break
    return tid_list


def fresh(campaign_name):
    campaign_info = RECOMMEND_CONF.get(campaign_name)
    if not campaign_info:
        return []
    group = campaign_info.get('group')
    if hasattr(settings, 'SPRING_GROUP'):
        group = settings.SPRING_GROUP
    for item in group:
        gid = item['gid']
        template = get_template(gid)
        latest_id = id_generator.generate_uuid(
            'activity:%s:%s' % (gid, template.current_term))
        item.update({
            'id': latest_id,
            'cover': template.cover or template.images.split(',')[0],
            'title': template.name
        })
    return group


def get_status(user_id, campaign_name):
    campaign_info = RECOMMEND_CONF.get(campaign_name)
    if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
        raise err.ParamError('campaign id invalid')
    now_time = datetime.strptime(utc_to_local_str(datetime.utcnow()), '%Y-%m-%d %H:%M:%S')
    date_str = now_time.strftime('%Y-%m-%d')
    campaign_status = campaign_db.get_status(user_id, campaign_name, date_str)
    return campaign_status


def activate(user_id, campaign_name):
    campaign_info = RECOMMEND_CONF.get(campaign_name)
    if not valid_time(campaign_info.get('start_time'), campaign_info.get('end_time')):
        raise err.ParamError('campaign id invalid')
    now_time = datetime.strptime(utc_to_local_str(datetime.utcnow()), '%Y-%m-%d %H:%M:%S')
    date_str = now_time.strftime('%Y-%m-%d')
    tid_list = _choose_coupon()
    coupon_list = campaign_db.activate(user_id, campaign_name, date_str, tid_list)
    return coupon_list


def get_award_timeline(campaign_name):
    a_list = []
    items = campaign_db.get_award_timeline(campaign_name)
    for item in items:
        user_id = item.user_id
        coupon_id = item.coupons.split(',')[0]
        account = get_account(user_id)
        coupon = get_coupon_by_id(coupon_id)
        a_list.append({
            'user_id': user_id,
            'nick_name': account.nick_name,
            'coupon_title': coupon.title,
            'coupon_desc': coupon.desc
        })
    return a_list


CURRENT_CAMPAIGN = 'children'


def query_tips(user_id):
    try:
        status = get_status(user_id, CURRENT_CAMPAIGN)
        return 1 if status else 0
    except:
        return 0
