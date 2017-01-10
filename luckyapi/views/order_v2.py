# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.cache import redis_cache
from luckycommon.credit.model.credit import AWARD_CREDIT_UNIT
from luckycommon.db.activity import get_activity
from luckycommon.pay import handler as pay_handler
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.limit import frequency_limit
from luckycommon.utils.exceptions import ParamError

from django.views.decorators.http import require_POST


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
        coupon = request.POST.get('coupon')
        pk_size = request.POST.get('pk_size', 0)
    except:
        raise ParamError('buy quantity parameter wrong')
    
    order_context = {}
    if request.user and request.user.extend:
        extend = json.loads(request.user.extend)
        for k in 'ip', 'addr':
            order_context[k] = extend.get(k)

    if coupon:
        order_context.update({'coupon': coupon})
    if pk_size is not None:
        order_context.update({'pk_size': pk_size})

    order, coupon = pay_handler.create_and_pay_order(request.user_id, activity_id, quantity, order_context)
    order_numbers = [] if not order.lucky_numbers else order.lucky_numbers.split(',')
    data = {
        'order_id': order.id,
        'order_num_count': len(order_numbers),
        'order_numbers': order_numbers
    }
    if coupon:
        data.update({'used_coupon': coupon.id})
    # check award credit
    award_credit = int(order.total_price) * AWARD_CREDIT_UNIT
    if coupon:
        award_credit = int(order.total_price - coupon.price) * AWARD_CREDIT_UNIT
    data.update({'award_credit': award_credit})
    _TRACKER.info({'user_id': order.buyer, 'type': 'pay',
                   'activity_id': order.activity_id,
                   'price': order.total_price,
                   'from': 'api'})
    
    return data 


@require_POST
@response_wrapper
@token_required
@frequency_limit
def batch_pay(request):
    """
    批量购买(购物车)
    """
    try:
        buy_list = json.loads(request.POST.get('buy_list'))
        coupon = request.POST.get('coupon')
    except:
        raise ParamError('pay list invalid')

    order_context = {}
    if request.user and request.user.extend:
        extend = json.loads(request.user.extend)
        for k in 'ip', 'addr':
            order_context[k] = extend.get(k)

    if coupon:
        order_context.update({'coupon': coupon})
    order_context.update({'from': 'api'})

    success_list, fail_list, coupon = pay_handler.batch_pay(request.user_id, buy_list, order_context)

    data = {
        'success_list': success_list,
        'fail_list': fail_list
    }
    if coupon:
        data.update({'used_coupon': coupon.id})
    # check award credit
    valid_amount = 0
    for item in success_list:
        valid_amount += item['order_num_count']
    if coupon:
        valid_amount -= coupon.price
    award_credit = valid_amount * AWARD_CREDIT_UNIT
    data.update({'award_credit': award_credit})
    return data
