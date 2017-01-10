# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import logging
from datetime import timedelta

from luckycommon.cache import redis_cache
from luckyapi.logic.crowdfunding import start_next_activity

from luckycommon.db import goods as goods_db
from luckycommon.db import activity as activity_db
from luckycommon.sunday.model.sunday import TIME_CONF

from luckycommon.utils.tz import local_now, local_to_utc


_LOGGER = logging.getLogger('worker')


def set_next_term():
    local_today = local_now().replace(hour=0, minute=0, second=0)
    weekday = local_today.date().weekday()
    this_sunday = local_today + timedelta(6 - weekday)
    next_term_id = '%d-%d-%d' % (this_sunday.year, this_sunday.month, this_sunday.day)
    # set stock
    for conf in TIME_CONF:
        template_id = conf['template_id']
        stock = conf['stock']
        template = activity_db.get_template(template_id)
        goods_id = template.goods_id
        goods = goods_db.get_goods(goods_id)
        total = goods.sold + stock
        goods_db.modify_good_info(int(goods_id), {'total': total})
        _LOGGER.info('auto sunday add stock %s to %s', goods_id, total)
    redis_cache.set_next_sunday_term(next_term_id)


def start_index(index):
    if index >= len(TIME_CONF):
        _LOGGER.warn('index %s out of TIME_CONF range', index)
    conf = TIME_CONF[index] 
    template_id = conf['template_id']
    activity = start_next_activity(0, template_id)
    _LOGGER.info('auto sunday start activity, id:%s', activity.id)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'set': 
        """
        每周六下午4点启动
        """
        set_next_term()
    if cmd == 'start':
        index = int(sys.argv[2])
        start_index(index)
