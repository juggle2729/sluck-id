# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.logic import receipt as receipt_handler

from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError

from django.utils.encoding import smart_unicode
from django.views.decorators.http import require_GET, require_POST


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@require_GET
@response_wrapper
@token_required
def get_receipts(request):
    """
    获取所有存储的收货地址 
    """
    user_id = request.user_id
    shipping_type = int(request.GET.get('shipping_type', 0))
    r_list = receipt_handler.view_receipt_address(user_id, shipping_type)
    return {
        'list': r_list
    }


@require_POST
@response_wrapper
@token_required
def add_receipt(request):
    """
    增加新的收货地址 
    """
    user_id = request.user_id
    try:
        data = smart_unicode(request.body)
        receipt_info = json.loads(data)
    except ValueError as e:
        raise ParamError('request body is not valid json.(%s)' % e)
    receipt_address = receipt_handler.add_receipt_address(user_id, receipt_info)
    return {
        'id': receipt_address.id
    }


@require_POST
@response_wrapper
@token_required
def modify_receipt(request, receipt_id):
    """
    修改收货地址 
    """
    user_id = request.user_id
    try:
        data = smart_unicode(request.body)
        receipt_info = json.loads(data)
    except ValueError as e:
        raise ParamError('request body is not valid json.(%s)' % e)
    receipt_address = receipt_handler.modify_receipt_address(user_id, receipt_id, receipt_info)
    return {}


@require_POST
@response_wrapper
@token_required
def remove_receipt(request, receipt_id):
    """
    删除存储的收货地址 
    """
    user_id = request.user_id
    shipping_type = int(request.GET.get('shipping_type', 0))
    receipt_handler.remove_receipt_address(user_id, receipt_id, shipping_type)
    return {}
