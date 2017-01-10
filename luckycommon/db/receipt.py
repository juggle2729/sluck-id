# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

from luckycommon.model import orm
from luckycommon.model.receipt import *

from luckycommon.utils.decorator import sql_wrapper


_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_receipt_address(user_id):
    return ReceiptAddress.query.filter(ReceiptAddress.user_id == user_id)\
                               .filter(ReceiptAddress.deleted == 0).all()


@sql_wrapper
def create_receipt_address(user_id, receipt_info):
    receipt_name = receipt_info.get('name')
    receipt_phone = receipt_info.get('phone')
    receipt_addr = receipt_info.get('address')
    receipt_addr_code = json.loads(receipt_info.get('addr_code'))
    is_default = receipt_info.get('default') or 0
    receipt_address = ReceiptAddress()
    receipt_address.user_id = user_id
    receipt_address.phone = receipt_phone
    receipt_address.name = receipt_name
    receipt_address.address = receipt_addr
    receipt_address.addr_code = json.dumps(receipt_addr_code, ensure_ascii=False)
    receipt_address.default = is_default
    receipt_address.save()
    if receipt_address.default == 1:
        ReceiptAddress.query.filter(ReceiptAddress.user_id == user_id)\
                            .filter(ReceiptAddress.id != receipt_address.id)\
                            .update({'default': 0})
        orm.session.commit()
    return receipt_address


@sql_wrapper
def update_receipt_address(user_id, receipt_id, receipt_info):
    item = ReceiptAddress.query.filter(ReceiptAddress.id == receipt_id)\
                               .filter(ReceiptAddress.user_id == user_id)\
                               .one() 
    item.name = receipt_info.get('name')
    item.phone = receipt_info.get('phone')
    item.address = receipt_info.get('address')
    receipt_addr_code = json.loads(receipt_info.get('addr_code'))
    item.addr_code = json.dumps(receipt_addr_code, ensure_ascii=False)
    item.default = receipt_info.get('default') or 0
    item.save()
    if item.default == 1:
        ReceiptAddress.query.filter(ReceiptAddress.user_id == user_id)\
                            .filter(ReceiptAddress.id != receipt_id)\
                            .update({'default': 0})
        orm.session.commit()
    return item


@sql_wrapper
def remove_receipt_address(user_id, receipt_id):
    ReceiptAddress.query.filter(ReceiptAddress.id == receipt_id)\
                        .filter(ReceiptAddress.user_id == user_id)\
                        .update({
                            'deleted': 1,
                            'updated_at': datetime.utcnow()
                        })
    orm.session.commit()


@sql_wrapper
def exists_receipt(user_id, receipt_id):
    return ReceiptAddress.query.filter(ReceiptAddress.user_id == user_id)\
                         .filter(ReceiptAddress.id == receipt_id)\
                         .first()


@sql_wrapper
def get_receipt_number(user_id, shipping_type):
    return ReceiptNumber.query.filter(ReceiptNumber.user_id == user_id)\
                              .filter(ReceiptNumber.shipping_type == shipping_type)\
                              .filter(ReceiptNumber.deleted == 0).all()


@sql_wrapper
def create_receipt_number(user_id, receipt_info):
    number = receipt_info.get('number')
    shipping_type = receipt_info.get('shipping_type')
    is_default = receipt_info.get('default') or 0
    receipt_number = ReceiptNumber()
    receipt_number.user_id = user_id
    receipt_number.shipping_type = shipping_type
    receipt_number.number = number
    receipt_number.default = is_default
    receipt_number.save()
    if receipt_number.default == 1:
        ReceiptNumber.query.filter(ReceiptNumber.user_id == user_id)\
                           .filter(ReceiptNumber.shipping_type == shipping_type)\
                           .filter(ReceiptNumber.id != receipt_number.id)\
                           .update({'default': 0})
        orm.session.commit()
    return receipt_number


@sql_wrapper
def update_receipt_number(user_id, receipt_id, receipt_info):
    item = ReceiptNumber.query.filter(ReceiptNumber.id == receipt_id)\
                              .filter(ReceiptNumber.user_id == user_id)\
                              .one() 
    item.number = receipt_info.get('number')
    item.default = receipt_info.get('default') or 0
    item.save()
    if item.default == 1:
        shipping_type = receipt_info.get('shipping_type')
        ReceiptNumber.query.filter(ReceiptNumber.user_id == user_id)\
                           .filter(ReceiptNumber.shipping_type == shipping_type)\
                           .filter(ReceiptNumber.id != receipt_id)\
                           .update({'default': 0})
        orm.session.commit()
    return item


@sql_wrapper
def remove_receipt_number(user_id, receipt_id):
    ReceiptNumber.query.filter(ReceiptNumber.id == receipt_id)\
                       .filter(ReceiptNumber.user_id == user_id)\
                       .update({
                           'deleted': 1,
                           'updated_at': datetime.utcnow()
                       })
    orm.session.commit()


@sql_wrapper
def exists_receipt_number(user_id, receipt_id):
    return ReceiptNumber.query.filter(ReceiptNumber.user_id == user_id)\
                        .filter(ReceiptNumber.id == receipt_id)\
                        .first()
