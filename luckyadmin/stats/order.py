# -*- coding: utf-8 -*-
import json
import logging

from django.views.decorators.http import require_GET

from luckycommon.order.db import order as db
from luckycommon.db.activity import get_activity, calc_prices, get_template
from luckycommon.utils.decorator import response_wrapper, mongo_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.stats import MG as mg
from luckycommon.utils.tz import get_utc_date
from luckycommon.utils.export import redirect_to_file, gen_filename


_LOGGER = logging.getLogger(__name__)


@require_GET
@response_wrapper
@token_required
def get_order_list(req):
    query_dct = req.GET.dict()
    export = query_dct.pop('$export', None)
    if export:
        filename = gen_filename('order')
        header = ['id', 'created_at', 'buyer', 'is_virtual', 'activity_id',
                  'activity_name', 'term_number', 'activity_status',
                  'activity_type', 'total_price', 'addr', 'ip']
        cn_header = ['id', u'创建时间', u'用户ID', u'自有用户', u'活动ID',
                     u'活动名', u'期数', u'活动状态', u'活动类型', u'总价',
                     u'用户地址', 'IP']
    resp_items = []
    items, total_count, _ = db.list_orders(query_dct, True)

    for item in items:
        order, is_virtual = item
        k = order.as_dict()
        activity = get_activity(k['activity_id'])
        k['id'] = str(k['id'])
        k['buyer'] = str(k['buyer'])
        if not export:
            template = get_template(activity.template_id)
            if template and template.short_title:
                k['activity_name'] = template.short_title
        if not k.get('activity_name'):
            k['activity_name'] = activity.name
        k['term_number'] = activity.term_number
        k['is_virtual'] = is_virtual
        k['activity_status'] = activity.status
        k['activity_type'] = 0 if activity.price == 0 else activity.unit
        k['updated_at'] = utc_to_local_str(k['updated_at'])
        k['created_at'] = utc_to_local_str(k['created_at'])
        k.update(json.loads(k['extend'] or '{}'))
        if export:
            resp_items.append([k.get(x, '-') for x in header])
        else:
            resp_items.append(k)
    if export:
        return redirect_to_file(resp_items, cn_header, filename)

    return {'list': resp_items, 'page': query_dct.get('$page', 1),
            'size': len(resp_items), 'total_count': total_count,
            'overview': get_order_overview()}


@mongo_wrapper
def get_order_overview():
    overview = {
        'total_price': 0,
        'total_count': 0,
    }
    lower = get_utc_date()
    total = mg.daily_stats.aggregate([
        {"$match": {"updated_at": {"$gte": lower}}},
        {"$group": {"_id": None, "total_count": {"$sum": 1},
                    "total_price": {"$sum": "$pay.total"}}}
    ])
    total = total.next() if total.alive else {}
    for k in overview:
        overview[k] = total.get(k, 0)
    prices = calc_prices()
    overview.update(prices)

    return overview
