# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from django.views.decorators.http import require_GET

from luckycommon.db.pay import list_pay, get_pay_overview, USER_TYPE
from luckycommon.db.activity import get_activity
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.tz import utc_to_local_str, utc_to_local
from luckycommon.utils.api import token_required
from luckycommon.utils.export import redirect_to_file, gen_filename


@require_GET
@response_wrapper
@token_required
def get_pay_list(req):
    query_dct = req.GET.dict()
    # only need finished pay
    if 'status' not in query_dct:
        query_dct['status'] = '2'
    export = query_dct.pop('$export', None)
    if export:
        filename = gen_filename('pay')
        header = ['id', 'created_at', 'user_id', 'user_type',
                  'pay_type', 'price', 'activity_name']
        cn_header = ['id', u'创建时间', u'用户ID', u'用户类型', u'充值类型', u'充值总额',
                     u'购买/充值']
    items, total_count = list_pay(query_dct)
    resp_items = []
    for item in items:
        # item: Pay, Account.created_at
        pay, user_created_at = item
        data = pay.as_dict()
        data['id'] = str(data['id'])
        if user_created_at:
            pay_at = utc_to_local(pay.created_at).date()
            registered_at = utc_to_local(user_created_at).date()
            if pay_at == registered_at:
                data['user_type'] = USER_TYPE['new_user']
            elif pay_at - registered_at == timedelta(days=1):
                data['user_type'] = USER_TYPE['next_day_user']
            elif pay_at - registered_at <= timedelta(days=6):
                data['user_type'] = USER_TYPE['week_user']
            else:
                data['user_type'] = USER_TYPE['old_user']

        data['created_at'] = utc_to_local_str(data['created_at'])
        data['updated_at'] = utc_to_local_str(data['updated_at'])
        if data['activity_id'] != '0' and data['activity_id'] is not None:
            activity = get_activity(data['activity_id'], need_fill=False)
            data['activity_name'] = activity.name if activity else u'(活动信息丢失)'
        elif data['activity_id'] == '0':
            data['activity_name'] = u'购物车'
        else:
            data['activity_name'] = '-'
        if export:
            resp_items.append([data.get(x, '-') for x in header])
        else:
            resp_items.append(data)

    if export:
        return redirect_to_file(resp_items, cn_header, filename)

    overview = get_pay_overview(query_dct)
    return {'list': resp_items, 'page': query_dct.get('$page', 1),
            'size': len(resp_items), 'total_count': total_count,
            'overview': overview}
