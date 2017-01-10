# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys


# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'
from luckycommon.model import orm
from luckycommon.order.model.order import RedEnvelope, AwardedOrder, ORDER_STATUS, SHIP_STATUS, RED_ENVELOPE_STATUS
from luckycommon.third.pingxx import check_redenvelope_status
from luckycommon.utils.tz import get_utc_date
from luckycommon.order.db import order as order_db

today = get_utc_date()
items = orm.session.query(RedEnvelope.order_id, RedEnvelope.third_id).join(
    AwardedOrder, AwardedOrder.order_id == RedEnvelope.order_id).filter(
    RedEnvelope.updated_at < today).filter(
    AwardedOrder.status == ORDER_STATUS.WAIT_SHIP).filter(
    RedEnvelope.status == RED_ENVELOPE_STATUS.EXCHANGED).all()

for item in items:
    order_id, third_id = item
    status = check_redenvelope_status(third_id)
    order_to = {}
    red_to = {}
    print order_id, ':', status
    if status == 'sent':
        order_to['status'] = ORDER_STATUS.WAIT_RECEIPT
    elif status in ('failed', 'refund'):
        order_to['ship_status'] = SHIP_STATUS.CHARGE_FAILED
        red_to['status'] = RED_ENVELOPE_STATUS.EXCHANGE_FAILED
    elif status == 'received':
        order_to['status'] = ORDER_STATUS.DEAL
    else:
        continue
    if order_to:
        order_db.update_order_by_id(order_id, order_to)
    if red_to:
        t = RedEnvelope.query.with_for_update().filter(
            RedEnvelope.order_id == order_id).one()
        t.status = red_to['status']
        t.save()
