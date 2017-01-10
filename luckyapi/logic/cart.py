# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.logic.crowdfunding import _UUID_RE, create_activity_lite

from luckycommon.cache import redis_cache
from luckycommon.model.activity import ACTIVITY_STATUS
from luckycommon.db.activity import get_activity

from luckycommon.utils.tz import now_ts
from luckycommon.utils.exceptions import ParamError, ResourceInsufficient


_LOGGER = logging.getLogger('lucky')

_MAX_COUNT = 10


def view_cart_list(user_id):
    cart_list = []
    cart_dict = redis_cache.list_cart(user_id)
    for activity_id, meta in cart_dict.items():
        meta_dict = json.loads(meta)
        number = int(meta_dict.get('number'))
        ts = int(meta_dict.get('ts'))

        if number <= 0:
            redis_cache.remove_cart(user_id, activity_id)
            continue
        activity = get_activity(activity_id)
        if activity.status != ACTIVITY_STATUS.STARTED:
            redis_cache.remove_cart(user_id, activity_id)
            continue
        left_amount = activity.target_amount - activity.current_amount
        if number > left_amount:
            number = left_amount

        cart_list.append({
            'ts': ts,
            'quantity': number,
            'lite': create_activity_lite(activity)
        })

    cart_list.sort(key=lambda x:x.get('ts'), reverse=False)
    return cart_list


def add_to_cart(user_id, cart_list):
    # 批量修改
    count = 0
    now = now_ts()
    edit_dict = {}
    return_list = []
    for cart_item in cart_list:
        activity_id = cart_item.get('activity_id')
        quantity = int(cart_item.get('quantity'))
        if quantity <= 0:
            continue
        activity = get_activity(activity_id)
        if activity.pk:
            continue
        if activity.status != ACTIVITY_STATUS.STARTED:
            continue
        count += 1
        if count > _MAX_COUNT:
            break

        left_amount = activity.target_amount - activity.current_amount
        if quantity > left_amount:
            quantity = left_amount
        item_value = json.dumps({'number': quantity, 'ts': now + count}, ensure_ascii=False)
        edit_dict.update({
            activity_id: item_value
        })
        cart_item.update({
            'ts': now + count,
            'quantity': quantity,
            'lite': create_activity_lite(activity)
        })
        del cart_item['activity_id']
        return_list.append(cart_item)

    if user_id:
        redis_cache.clear_cart_list(user_id)
        if edit_dict:
            redis_cache.edit_cart_list(user_id, edit_dict)
    return return_list
