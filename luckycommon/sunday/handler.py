# -*- coding: utf-8 -*-
import json
import time
import logging
from datetime import datetime, timedelta

from luckycommon.cache import redis_cache

from luckycommon.model.activity import ACTIVITY_STATUS

from luckycommon.db.goods import get_goods
from luckycommon.db import activity as activity_db

from luckycommon.sunday.model.sunday import TIME_CONF, STATUS
from luckycommon.sunday.db import sunday as sunday_db

from luckycommon.utils.tz import now_ts, to_local_ts
from luckycommon.utils.exceptions import ParamError


_LOGGER = logging.getLogger('lucky')


def apply_sunday(user_id):
    term_id = redis_cache.get_current_sunday_term()
    if not term_id:
        raise ParamError()
    sunday_db.apply_user(user_id, term_id)


def get_sunday_status(user_id):
    data = {}
    term_id = redis_cache.get_current_sunday_term()
    if not term_id:
        return None
    user_apply = sunday_db.get_apply(user_id, term_id)
    applied = True if user_apply else False
    a_list = []
    for conf in TIME_CONF:
        template_id = conf['template_id']
        template = activity_db.get_template(template_id)
        current_term = template.current_term
        latest_activity = activity_db.get_activity(None, template_id, current_term, need_fill=False)
        goods_id = template.goods_id
        goods = get_goods(goods_id)
        left_stock = goods.total - goods.sold
        if latest_activity and latest_activity.status == ACTIVITY_STATUS.STARTED:
            left_stock += 1
            current_status = STATUS.ONGOING
        elif left_stock > 0:
            current_status = STATUS.NOTSTART
        else:
            current_status = STATUS.DONE
        max_stock = conf['stock']
        if left_stock > max_stock:
            left_stock = max_stock
        a_list.append({
            'gid': template_id,
            'cover': template.cover,
            'name': template.name,  
            'max_stock': max_stock,
            'left_stock': left_stock,
            'status': current_status,
            'start_time': conf['start_time']
        })
    term_year, term_month, term_day = term_id.split('-')
    start_date = datetime(int(term_year), int(term_month), int(term_day))
    end_date = start_date + timedelta(1)
    # hard code here, 默认10点30分开启第一场
    start_ts = to_local_ts(start_date.replace(hour=10, minute=30))
    end_ts = to_local_ts(end_date)
    data = {
        'term_id': term_id,
        'now_ts': now_ts(),
        'start_ts': start_ts,
        'end_ts': end_ts,
        'applied': applied,
        'a_list': a_list
    }
    return data
