# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.order.handler import (view_buy_record_list,
                                       view_order_detail,
                                       view_current_status,
                                       view_available_red_envelopes,
                                       update_award_order,
                                       affirm_receipt_order)
from luckycommon.push import handler as push_handler
from luckycommon.pay import handler as pay_handler
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.limit import frequency_limit
from luckycommon.utils.exceptions import ParamError, AuthenticateError

from django.conf import settings
from django.utils.encoding import smart_unicode
from django.views.decorators.http import require_GET, require_POST


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@require_POST
@response_wrapper
@token_required
@frequency_limit
def pay(request, activity_id):
    """
    购买商品（使用余额）
    """
    try:
        quantity = int(request.POST.get('buy_quantity'))
        if quantity < 1:
            raise
    except:
        raise ParamError('`buy_quantity` parameter wrong')

    order_context = {}
    if request.user and request.user.extend:
        extend = json.loads(request.user.extend)
        for k in 'ip', 'addr':
            order_context[k] = extend.get(k)

    order, coupon = pay_handler.create_and_pay_order(
        request.user_id, activity_id, quantity, order_context)
    buy_record_list, count = view_buy_record_list(
        request.user_id, 0, 0, order.activity_id)
    data = {
        'order_id': order.id,
        'order_numbers': [] if not order.lucky_numbers else order.lucky_numbers.split(','),
        'total_record': buy_record_list
    }
    _TRACKER.info({'user_id': order.buyer, 'type': 'pay',
                   'activity_id': order.activity_id,
                   'price': order.total_price,
                   'from': 'api'})

    return data


@require_POST
@response_wrapper
@token_required
def award(request, order_id):
    """
    领奖（提交收货地址）
    """
    if not request.user_id:
        raise AuthenticateError('not login')

    try:
        data = smart_unicode(request.body)
        receipt_info = json.loads(data)
    except ValueError as e:
        raise ParamError('request body is not valid json.(%s)' % e)

    update_award_order(request.user_id, order_id, receipt_info)

    return {}


@require_POST
@response_wrapper
@token_required
def deal(request, order_id):
    """
    确认收货
    """
    if not request.user_id:
        raise AuthenticateError('not login')

    affirm_receipt_order(request.user_id, order_id)
    return {}


@require_GET
@response_wrapper
@token_required
def current_status(request, activity_id, order_id):
    """
    订单当前状态
    """
    user_id = request.user_id
    order_info = view_current_status(user_id, activity_id, order_id)
    data = {
        'info': order_info,
    } 
    return data


@require_GET
@response_wrapper
@token_required
def get_order_detail(request, order_id):
    """
    获取订单详情
    """
    data = view_order_detail(request.user_id, order_id)
    return data


@require_GET
@response_wrapper
@token_required
def get_available_passcard(request):
    """
    获取可用的卡密列表
    """
    user_id = request.user_id
    r_list = view_available_red_envelopes(user_id)
    return {
        'list': r_list
    }
