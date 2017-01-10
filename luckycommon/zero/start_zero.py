# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import json
import logging
from datetime import timedelta, datetime

from luckyapi.logic.crowdfunding import start_next_activity

from luckycommon.cache import redis_cache

from luckycommon.zero.model.zero import TIME_CONF, TEMPLATE_ID

from luckycommon.db import goods as goods_db
from luckycommon.db import activity as activity_db
from luckycommon.utils import tz

_LOGGER = logging.getLogger('lucky')


def add_stock(goods_id):
    goods = goods_db.get_goods(goods_id)
    total = goods.sold + 1
    goods_db.modify_good_info(int(goods_id), {'total': total})
    _LOGGER.info('auto zero add stock %s to %s', goods_id, total)


def start_activity(template_id, goods_id, name, short_title, target_amount, cover, images, graphics):
    query_dct = {
        'status': 1,
        'name': name,
        'goods_id': goods_id,
        'short_title': short_title,
        'target_amount': target_amount,
        'cover': cover,
        'images': images,
        'graphics': graphics
    }
    need_start = activity_db.update_template(template_id, query_dct)
    _LOGGER.info('auto zero update template %s to %s', template_id, name)
    activity = start_next_activity(0, template_id)
    _LOGGER.info('auto zero start activity, id:%s', activity.id)
    return activity


def start():
    now = datetime.now()
    print now
    print TIME_CONF
    hour = now.hour
    for index, conf in enumerate(TIME_CONF):
        print hour, conf['hour']
        if hour == conf['hour']:
            # do it
            zero_conf = conf['info']
            goods_id = zero_conf['goods_id']
            name = zero_conf['name']
            short_title = zero_conf['short_title']
            target_amount = zero_conf['target_amount']
            cover = zero_conf['cover']
            images = zero_conf['images']
            graphics = zero_conf['graphics']
            add_stock(goods_id)
            activity = start_activity(TEMPLATE_ID, goods_id, name, short_title, target_amount, cover, images, graphics)
            # update count down for next activity
            next_index = index + 1 if index + 1 < len(TIME_CONF) else 0
            next_conf = TIME_CONF[next_index]
            next_hour = next_conf['hour']
            if next_index == 0:
                next_time = now + timedelta(days=1)
            else:
                next_time = now
            next_time = next_time.replace(hour=next_hour, minute=0, second=0, microsecond=0)
            cache_info = {
                'index': next_index,
                'ts': tz.to_local_ts(next_time),
                'template_id': TEMPLATE_ID,
                'term_number': activity.term_number + 1,
                'info': json.dumps(next_conf['info'], ensure_ascii=False)
            }
            print cache_info
            redis_cache.update_zero_time(cache_info)
            _LOGGER.info('updated count down for next index:%s', next_index)


if __name__ == "__main__":
    start()
