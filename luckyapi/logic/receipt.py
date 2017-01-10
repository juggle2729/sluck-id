# -*- coding: utf-8 -*-
import logging

from luckycommon.db import receipt as receipt_db
from luckycommon.utils import exceptions as err
from luckycommon.utils.respcode import StatusCode


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')

_MAX_ADDR_SIZE = 20
_MAX_NUM_SIZE = 3


def view_receipt_address(user_id, shipping_type):
    r_list = []
    if not shipping_type:
        receipt_items = receipt_db.get_receipt_address(user_id)
        for item in receipt_items:
            r_list.append({
                'id': item.id,
                'phone': item.phone,
                'name': item.name,
                'address': item.address,
                'addr_code': item.addr_code,
                'default': item.default,
            }) 
    else:
        receipt_items = receipt_db.get_receipt_number(user_id, shipping_type)
        for item in receipt_items:
            r_list.append({
                'id': item.id,
                'number': item.number,
                'shipping_type': item.shipping_type,
                'default': item.default,
            })
    return r_list


def add_receipt_address(user_id, receipt_info):
    shipping_type = receipt_info.get('shipping_type')
    if not shipping_type:
        receipt_items = receipt_db.get_receipt_address(user_id)
        if len(receipt_items) >= _MAX_ADDR_SIZE:
            raise err.ParamError('reached limit', status=StatusCode.REACH_LIMIT)
    else:
        receipt_items = receipt_db.get_receipt_number(user_id, shipping_type)
        if len(receipt_items) >= _MAX_NUM_SIZE:
            raise err.ParamError('reached limit', status=StatusCode.REACH_LIMIT)
    try:
        if not shipping_type:
            receipt_address = receipt_db.create_receipt_address(user_id, receipt_info)
        else:
            receipt_address = receipt_db.create_receipt_number(user_id, receipt_info)
    except Exception as e:
        _LOGGER.exception('add receipt address exception, %s', e)
        raise err.ParamError()
    return receipt_address


def modify_receipt_address(user_id, receipt_id, receipt_info):
    shipping_type = receipt_info.get('shipping_type')
    if not shipping_type:
        receipt_address = receipt_db.update_receipt_address(user_id, receipt_id, receipt_info)
    else:
        receipt_address = receipt_db.update_receipt_number(user_id, receipt_id, receipt_info)
    return receipt_address


def remove_receipt_address(user_id, receipt_id, shipping_type):
    if not shipping_type:
        receipt_db.remove_receipt_address(user_id, receipt_id)
    else:
        receipt_db.remove_receipt_number(user_id, receipt_id)


def valid_receipt_address(user_id, receipt_id, shipping_type=None):
    if not shipping_type:
        return receipt_db.exists_receipt(user_id, receipt_id)
    else:
        return receipt_db.exists_receipt_number(user_id, receipt_id)
