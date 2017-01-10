# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import logging

from luckyapi.logic.crowdfunding import start_next_activity

from luckycommon.db import goods as goods_db
from luckycommon.db import activity as activity_db


_LOGGER = logging.getLogger('worker')


CARD_CONF = (
    ( # 10:00 AM 
        {'tid': 506, 'goods_id': 520, 'stock': 500},
        {'tid': 460, 'goods_id': 474, 'stock': 300},
        {'tid': 461, 'goods_id': 475, 'stock': 250},
        {'tid': 462, 'goods_id': 476, 'stock': 200},
        {'tid': 463, 'goods_id': 477, 'stock': 150},
    ),
    ( # 15:00 AM
        {'tid': 506, 'goods_id': 520, 'stock': 500},
        {'tid': 460, 'goods_id': 474, 'stock': 300},
        {'tid': 461, 'goods_id': 475, 'stock': 250},
        {'tid': 462, 'goods_id': 476, 'stock': 200},
        {'tid': 463, 'goods_id': 477, 'stock': 150},
    ),
    ( # 20:00 AM
        {'tid': 506, 'goods_id': 520, 'stock': 500},
        {'tid': 460, 'goods_id': 474, 'stock': 300},
        {'tid': 461, 'goods_id': 475, 'stock': 250},
        {'tid': 462, 'goods_id': 476, 'stock': 200},
        {'tid': 463, 'goods_id': 477, 'stock': 150},
    ),
)


def add_stock(goods_id, stock):
    goods = goods_db.get_goods(goods_id)
    total = goods.total + stock
    goods_db.upsert_goods({'total': total}, int(goods_id))
    _LOGGER.info('auto card add stock %s to %s', goods_id, total)


def start_activity(template_id):
    template = activity_db.get_template(template_id)
    if template.status != 1:
        query_dct = {
            'status': 1,
        }
        need_start = activity_db.update_template(template_id, query_dct)
        _LOGGER.info('auto card update template %s', template_id)
        activity = start_next_activity(0, template_id)
        _LOGGER.info('auto card start activity, id:%s', activity.id)


def start(index):
    card_list = CARD_CONF[index]
    for card_conf in card_list:
        template_id = card_conf['tid']
        goods_id = card_conf['goods_id']
        stock = card_conf['stock']
        add_stock(goods_id, stock)
        start_activity(template_id)


if __name__ == "__main__":
    index = int(sys.argv[1])
    start(index)
