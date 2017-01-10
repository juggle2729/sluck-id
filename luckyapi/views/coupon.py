# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.logic import coupon as coupon_handler
from luckyapi.logic import crowdfunding as activity_handler

from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError

from django.views.decorators.http import require_GET, require_POST

from future.utils import raise_with_traceback


_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
@token_required
def get_my_coupons(request):
    """
    查看我的红包
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        status = int(request.GET['status']) if request.GET.get('status') else None
    except Exception as e:
        raise_with_traceback(ParamError(e))

    c_list, count = coupon_handler.view_user_coupons(request.user_id, status, page, size)
    data = {
        'list': c_list,
        'total_count': count
    }
    return data


@require_GET
@response_wrapper
@token_required
def get_available_coupons(request):
    """
    获取可用红包
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        price = int(request.GET['price'])
        buy_list = request.GET.get('buy_list')
        if buy_list:
            buy_list = json.loads(buy_list)
    except Exception as e:
        raise_with_traceback(ParamError(e))

    if buy_list:
        buy_list = activity_handler.view_tids_by_aids(buy_list)
    a_list, u_list = coupon_handler.view_available_coupons(request.user_id, price, buy_list, page, size)
    data = {
        'list': a_list,
        'pending_list': u_list,
        'total_count': len(a_list) 
    }
    return data


@require_POST
@response_wrapper
def snatch_group_coupon(request, group_coupon_id):
    """
    抢红包
    """
    phone_number = request.POST.get('phone')
    if not phone_number or len(phone_number) != 11 or not phone_number.startswith('1'):
        raise ParamError('phone number invalid')
    data = coupon_handler.snatch_coupon(phone_number, group_coupon_id)
    return data
