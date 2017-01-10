# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

from sqlalchemy import func

from luckycommon.model import orm
from luckycommon.order.model.order import ChargeCardAward, ChargeCardPool
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.third.kamen import card_decrypt

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_card_info(order_id):
    info = ChargeCardAward.query.filter(
        ChargeCardAward.order_id == order_id).one()
    info = info.as_dict()
    info['card_info'] = json.loads(info['card_info'] or '[]')
    for k in info['card_info']:
        k['card_number'] = card_decrypt(k['third_id'], k['card_number'])
    return info


@sql_wrapper
def get_kamen_stocks():
    items = orm.session.query(ChargeCardPool.product_id, ChargeCardPool.title,
                              func.count(ChargeCardPool)).filter(
        ChargeCardPool.used == 0).group_by(ChargeCardPool.product_id)
    resp_items = []
    for item in items:
        resp_items.append({
            'product_id': item[0],
            'title': item[1][2:-2],
            'count': int(item[2])
        })
    return resp_items


@sql_wrapper
def remove_card(user_id, order_id):
    ChargeCardAward.query.filter(ChargeCardAward.order_id == order_id).filter(
        ChargeCardAward.user_id == user_id).update({
            'deleted': 1,
            'updated_at': datetime.utcnow()
        })
    orm.session.commit()
