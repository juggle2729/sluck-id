# -*- coding: utf-8 -*-
from django.views.decorators.http import require_GET

from luckycommon.db import activity as activity_db
from luckycommon.model.activity import ACTIVITY_STATUS
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.cache.redis_cache import (get_virtual_account,
                                           get_left_numbers_count)
from luckyapi.logic.crowdfunding import (create_activity_lite,
                                         view_activity_detail)
from luckycommon.order.handler import view_buy_record_list
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.export import redirect_to_file, gen_filename


@require_GET
@response_wrapper
@token_required
def get_activities(req):
    query_dct = req.GET.dict()
    page = int(query_dct.get('page', 0))
    size = int(query_dct.get('size', 0))
    limit = 20 if size <= 0 else size
    offset = 0 if page <= 0 else (page - 1) * limit
    items, total_count = activity_db.get_hot_activitys(limit, offset)

    resp_items = []
    for item in items:
        resp_items.append(create_activity_lite(item))

    return {'list': resp_items, 'page': page or 1,
            'size': len(resp_items), 'total_count': total_count}


@require_GET
@response_wrapper
@token_required
def get_activities_plus(req):
    ''' for web console, much more info
    '''
    query_dct = req.GET.dict()
    export = query_dct.pop('$export', None)
    if export:
        filename = gen_filename('activity')
        header = ['name', 'created_at', 'template_id', 'price', 'unit',
                  'status', 'term_number', 'target_amount', 'current_amount',
                  'virtual_amount', 'buyer_count', 'virtual_count', 'max_real',
                  'max_virtual', 'announced_at', 'winner', 'is_winner_virtual']
        cn_header = [u'活动名', u'创建时间', u'模板名', u'价格', u'单位', u'状态',
                     u'期数', u'目标数量', u'当前购买量', u'自有用户购买量', u'总用户数',
                     u'自有用户数', u'渠道用户最大购买人次', u'自有用户最大购买人次',
                     u'开奖时间', u'中奖者', u'自有用户中奖']
    resp_items = []
    items, total_count = activity_db.list_activities(query_dct)
    virtual_users = get_virtual_account()
    for item in items:
        # item: Activity, winner_id, is_virtual
        data, winner_id, is_virtual = item
        data.updated_at = utc_to_local_str(data.updated_at)
        data.created_at = utc_to_local_str(data.created_at)
        data.announced_at = utc_to_local_str(data.announced_at)
        if not export:
            template = activity_db.get_template(data.template_id)
            if template and template.short_title:
                data.name = template.short_title
        data = data.as_dict()
        if data['status'] == ACTIVITY_STATUS.ANNOUNCED:
            data['is_winner_virtual'] = is_virtual
            data['current_amount'] = data['target_amount']
        elif data['status'] == ACTIVITY_STATUS.STARTED:
            data['current_amount'] = data['target_amount'] - \
                get_left_numbers_count(data['id'])
        elif data['status'] == ACTIVITY_STATUS.ANNOUNCE_READY:
            data['current_amount'] = data['target_amount']
        buyers = activity_db.get_activity_users(data['id'])
        max_virtual = 0
        max_real = 0
        data['virtual_count'] = data['virtual_amount'] = 0
        for buyer in buyers:
            price = (len(buyer.numbers) + 1) / 9
            if buyer.user_id == winner_id:
                data['winner_buy_count'] = price
            if str(buyer.user_id) in virtual_users:
                data['virtual_count'] += 1
                data['virtual_amount'] += price
                if price > max_virtual:
                    max_virtual = price
            elif price > max_real:
                max_real = price
        data['buyer_count'] = len(buyers)
        data['max_virtual'] = max_virtual
        data['max_real'] = max_real
        data['winner'] = winner_id
        if export:
            resp_items.append([data.get(x, '-') for x in header])
        else:
            resp_items.append(data)

    if export:
        return redirect_to_file(resp_items, cn_header, filename)
    overview = activity_db.get_activities_overview()
    return {'list': resp_items, 'page': query_dct.get('$page', 1),
            'size': len(resp_items), 'total_count': total_count,
            'overview': overview}


@require_GET
@response_wrapper
@token_required
def get_activity(req, activity_id):
    detail = view_activity_detail(None, activity_id)
    activities = activity_db.get_activity_users(activity_id)
    virtual_users = get_virtual_account()
    for k in 'virtual_count', 'virtual_price', 'real_price':
        detail[k] = 0
    for ac in activities:
        price = (len(ac.numbers) + 1) / 9
        if str(ac.user_id) in virtual_users:
            detail['virtual_count'] += 1
            detail['virtual_price'] += price
        else:
            detail['real_price'] += price

    detail['real_count'] = len(activities) - detail['virtual_count']

    return detail


@require_GET
@response_wrapper
@token_required
def get_buy_record(req, activity_id):
    query_dct = req.GET.dict()
    page = int(query_dct.get('page', 0))
    size = int(query_dct.get('size', 0))

    items, total_count = view_buy_record_list(
        None, page, size, activity_id, True)

    return {'list': items, 'page': page or 1,
            'size': len(items), 'total_count': total_count}
