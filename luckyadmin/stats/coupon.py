# -*- coding: utf-8 -*-
from django.views.decorators.http import require_GET

from luckycommon.db.coupon import get_coupon_overview, get_coupon
from luckycommon.db.activity import get_activity
from helper import list_object
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import ts_to_local_date_str
from luckycommon.utils.export import redirect_to_file, gen_filename
from luckycommon.stats import MG as mg


@require_GET
@response_wrapper
@token_required
def get_coupons(req):
    return get_coupon_overview()


@require_GET
@response_wrapper
@token_required
def get_coupon_list(req):
    query_dct = req.GET.dict()
    export = query_dct.pop('$export', None)
    if export:
        filename = gen_filename('coupon')
        header = ['user_id', 'coupon_type', 'desc', 'price', 'status',
                  'start_ts', 'expire_ts', 'from', 'target']
        cn_header = [u'用户ID', u'红包种类', u'描述', u'价格', u'状态',
                     u'生效时间', u'过期时间', u'来源', u'用途']
    items, total_count = list_object(query_dct, mg.coupon)
    resp_items = []
    for item in items:
        if 'start_ts' not in item:
            item.update(get_coupon(item['_id'], item[
                        'user_id'], False).as_dict())
        item['start_ts'] = ts_to_local_date_str(
            item['start_ts'], f="%Y-%m-%d %H:%M:%S")
        item['expire_ts'] = ts_to_local_date_str(
            item['expire_ts'], f="%Y-%m-%d %H:%M:%S")
        if item.get('target'):
            target = item['target']
            if isinstance(target, list):
                item['target'] = u'购物车'
            else:
                ac = get_activity(item['target'], need_fill=False)
                item['target'] = ac.name if ac else u'(活动数据丢失)'
        if export:
            resp_items.append([item.get(x, '-') for x in header])
        else:
            resp_items.append(item)
    if export:
        return redirect_to_file(resp_items, cn_header, filename)

    return {'list': resp_items, 'page': query_dct.get('$page', 1),
            'size': len(resp_items), 'total_count': total_count,
            'overview': get_coupon_overview()}
