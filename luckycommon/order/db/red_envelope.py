# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.utils.tz import local_now
from luckycommon.order.model import orm
from luckycommon.order.model.order import (AwardedOrder, RedEnvelope,
                                           ORDER_STATUS)
from luckycommon.order.db.order import encoding_code
from luckycommon.db.helper import (get_orderby, parse_query_dct,
                                   paginate, generate_filter, get_count)
from luckycommon.utils.decorator import sql_wrapper

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def list_red_envelopes(query_dct):
    id_filter = query_dct.get('id')
    if id_filter is not None:
        query_dct['id'] = encoding_code(id_filter)
    order_status = query_dct.pop('order_status', None)
    query = orm.session.query(RedEnvelope, AwardedOrder.status).join(
        AwardedOrder, RedEnvelope.order_id == AwardedOrder.order_id)
    if order_status is not None:
        query = query.filter(AwardedOrder.status == int(order_status))
    query_dct = parse_query_dct(query_dct, RedEnvelope)
    query = query.filter(generate_filter(query_dct, RedEnvelope))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), RedEnvelope)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)

    return query.all(), total_count


@sql_wrapper
def manual_sent_redenvelops(data, by=None):
    if not data:
        return
    for order_id, in data:
        try:
            order_id = long(order_id)
        except ValueError:
            _LOGGER.warning('skip "%s" when import', order_id)
            continue
        order = AwardedOrder.query.with_for_update().filter(
            AwardedOrder.order_id == order_id).first()
        if not order or order.status not in (
                ORDER_STATUS.WAIT_SHIP, ORDER_STATUS.WAIT_RECEIPT):
            continue
        extend = json.loads(order.extend or '{}')
        extend['send_time'] = local_now().strftime('%Y-%m-%d %H:%M:%S')
        if by:
            extend['send_by'] = by
        order.status = ORDER_STATUS.DEAL
        order.extend = json.dumps(extend, ensure_ascii=False)
        order.save()
