# -*- coding: utf-8 -*-
from __future__ import absolute_import

import datetime
import logging
import os
import sys

import tablib

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.order.model.order import *
from luckycommon.level.handler import get_user_level
from luckycommon.db.activity import get_activity
from luckycommon.cache import redis_cache
from luckycommon.stats import MG as mg
from luckycommon.utils import tz
from luckycommon.utils.mail import TOOL_MAIL_SENDER

_LOGGER = logging.getLogger('worker')

EXPORT_PATH = '/home/ubuntu/af-env/data/stats/'
USER_TYPE = {
    'new_user': 1,
    'next_day_user': 2,
    'week_user': 3,
    'old_user': 4,
}


def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path


cmd = sys.argv[1]
if cmd == 'start':
    days_ago = int(sys.argv[2])
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=days_ago)
    start_date = start_date.replace(hour=16, minute=0, second=0, microsecond=0)
    end_date = now - datetime.timedelta(days=days_ago - 1)
    end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)

    order_list = []
    items = Order.query.filter(Order.created_at > start_date).filter(Order.created_at < end_date).all()
    for item in items:
        order_id = item.id
        user_id = item.buyer
        if redis_cache.is_virtual_account(user_id):
            continue
        user_level = get_user_level(user_id)['current_level']
        order_time = tz.utc_to_local_str(item.created_at)
        aid = item.activity_id
        activity = get_activity(aid)
        number_count = item.goods_quantity
        user_stats = mg.user_stats.find_one({'_id': user_id})
        if not user_stats:
            continue
        chn = user_stats.get('chn')
        user_type = u'未知'
        if user_stats.get('created_at'):
            pay_at = tz.utc_to_local(item.created_at).date()
            registered_at = tz.utc_to_local(user_stats['created_at']).date()
            if pay_at == registered_at:
                user_type = u'新用户'
            elif pay_at - registered_at == datetime.timedelta(days=1):
                user_type = u'次日用户'
            elif pay_at - registered_at <= datetime.timedelta(days=6):
                user_type = u'周用户'
            else:
                user_type = u'老用户'
        order_list.append((order_id, order_time, user_id, chn, user_type, user_level, activity.short_title,
                           activity.term_number, activity.target_amount, number_count))
    excel_header = [u'订单id', u'创建时间', u'uid', u'chn', u'用户属性', u'vip等级', u'商品简称', u'商品期数', u'活动总需人次', u'本次参与人次']
    file_path = redirect_to_file(order_list, excel_header, u'order_daily_data_%s.xlsx' % end_date.strftime('%y-%m-%d'))
    TOOL_MAIL_SENDER.send(u"[%s]每日订单汇总" % end_date.strftime('%y-%m-%d'), u'详情请见附件', attachments=[file_path])
