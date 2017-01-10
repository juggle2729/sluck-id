# -*- coding: utf-8 -*-
import logging

from luckycommon.push import handler as push_handler
from luckycommon.cache import redis_cache

from luckycommon.order.model.order import AwardedOrder, ORDER_STATUS
from luckycommon.order.db import order as order_db
from luckycommon.order.handler import show_order
from luckycommon.model.shipping import AutoShipping
from luckycommon.model.receipt import SHIPPING_TYPE
from luckycommon.db.goods import get_goods
from luckycommon.db.activity import get_activity, get_activity_users, get_activity_win
from luckycommon.db.transaction import add_system_award_transaction

from django.conf import settings

_LOGGER = logging.getLogger('worker')


def shipping_coin(activity):
    activity_win = get_activity_win(activity.id)
    await_order = order_db.get_awarded_order(activity_win.order_id)
    user_id = await_order.user_id
    if redis_cache.is_virtual_account(user_id):
        return
    recharge_price = float(get_goods(activity.goods_id).price)
    _LOGGER.info('begin recharge, %s, %s', activity.id, await_order.order_id)
    try:
        # 加锁
        item = AutoShipping.query.filter(
            AutoShipping.order_id == await_order.order_id).with_lockmode(
            'update').first()
        if not item:
            item = AutoShipping()
            item.order_id = await_order.order_id
            item.template_id = activity.template_id
            item.user_id = user_id
            item.phone = 'coin'
            item.price = recharge_price
            item.status = 0
            item.shipping_type = SHIPPING_TYPE.COIN
            item.save()
            order_db.update_order_info(
                await_order.order_id,
                {
                    'status': ORDER_STATUS.DEAL,
                })
            add_system_award_transaction(
                user_id, award_amount=recharge_price, title='Lucky Coins')
            item.status = 1
            item.save()
            push_handler.push_shipping(
                await_order.order_id, {'express': 'coin'})
            show_order(await_order)
            _LOGGER.info('finish recharge %s coin %s for %s',
                         recharge_price, await_order.order_id, user_id)
            return
    except Exception as e:
        _LOGGER.exception('send coin to user exception, %s-%s, %s',
                          user_id, await_order.order_id, e)
