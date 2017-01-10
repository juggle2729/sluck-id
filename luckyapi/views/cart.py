# -*- coding: utf-8 -*-
import json
import logging

from django.views.decorators.http import require_GET, require_POST

from luckyapi.logic.cart import view_cart_list, add_to_cart

from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError

from future.utils import raise_with_traceback


_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
@token_required
def list_cart(req):
    """
    获取购物车清单
    eg:
    {
        'size': 10,
        'list': [
            {
                'lite': ActivityLite,
                'quantity': 1
            }
        ]
    }
    """
    cart_list = view_cart_list(req.user_id)
    data = {
        'size': len(cart_list),
        'list': cart_list
    }
    return data


@require_POST
@response_wrapper
def edit_cart(req):
    """
    编辑购物车(批量编辑)
    """
    try:
        cart_list = req.POST.get('list')
        cart_list = json.loads(cart_list)
    except Exception as e:
        raise_with_traceback(ParamError(e))

    cart_list = add_to_cart(req.user_id, cart_list)
    data = {
        'size': len(cart_list),
        'list': cart_list
    }
    return data
