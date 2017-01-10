# -*- coding: utf-8 -*-
import hashlib
import json
import logging

import requests

from luckycommon.order.db import order as order_db
from luckycommon.order.model.order import ORDER_STATUS, SHIP_STATUS
from luckycommon.model.shipping import AutoShipping
from luckycommon.push import handler as push_handler

_LOGGER = logging.getLogger('juhe')
_TRACKER = logging.getLogger('tracker')

APP_KEY = 'ea7ec2a3724b89e8c12a7cebb4186c86'
RECHARGE_API = 'http://op.juhe.cn/ofpay/mobile/onlineorder?key=ea7ec2a3724b89e8c12a7cebb4186c86&phoneno=%s&cardnum=%s&orderid=%s&sign=%s'
OPEN_ID = 'JH14c4a9c19c272ed8a7f716749f58a3e5'


def recharge(order_id, template_id, user_id, phone, price):
    item = AutoShipping.query.filter(
        AutoShipping.order_id == order_id).with_lockmode('update').first()
    if not item:
        item = AutoShipping()
        item.order_id = order_id
        item.template_id = template_id
        item.user_id = user_id
        item.phone = phone
        item.price = price
        item.status = 0
    else:
        return 2 if item.status == 2 else -1
    item.save()
    if phone.startswith('86'):
        phone_no = phone[2:]
    else:
        phone_no = phone
    card_num = int(price)
    order_no = str(order_id) + str(user_id)
    md5_str = OPEN_ID + APP_KEY + str(phone_no) + str(card_num) + order_no
    signed_str = hashlib.md5(md5_str).hexdigest()
    recharge_api = RECHARGE_API % (phone_no, card_num, order_no, signed_str)
    _LOGGER.info('request recharge, url:%s', recharge_api)
    try:
        r = requests.get(recharge_api)
        item = AutoShipping.query.filter(
            AutoShipping.order_id == order_id).with_lockmode('update').first()
        item.response = r.text
        response_obj = json.loads(r.text)
        error_code = response_obj.get('error_code')
        if error_code != 0:
            item.status = 2
            _LOGGER.error('request recharge response error, %s', r.text)
        item.save()
    except Exception as e:
        _LOGGER.exception('requests recharge fail, %s', e)
    return item.status


def change_order(order_id, success):
    if success:
        # update order
        order_db.update_order_by_id(
            order_id,
            {
                'status': ORDER_STATUS.WAIT_RECEIPT,
                'ship_status': SHIP_STATUS.NORMAL
            })
        # push shipping
        push_handler.push_shipping(order_id, {})
        _LOGGER.info('push shipping success, %s', order_id)
    else:
        order_db.update_order_by_id(
            order_id,
            {
                'status': ORDER_STATUS.WAIT_SHIP,
                'ship_status': SHIP_STATUS.CHARGE_FAILED
            })


def verify(sign, sporder_id, order_no):
    md5_str = APP_KEY + str(sporder_id) + str(order_no)
    signed_str = hashlib.md5(md5_str).hexdigest()
    return sign == signed_str


def check_notify_sign(request):
    sporder_id = request.POST.get('sporder_id')
    order_no = request.POST.get('orderid')
    status = int(request.POST.get('sta'))
    sign = request.POST.get('sign')
    isSign = verify(sign, sporder_id, order_no)
    _LOGGER.info("juhe check_notify_sign, sporder_id:%s, order_no: %s, trade_status:%s, isSign: %s",
                 sporder_id, order_no, status, isSign)
    if isSign:
        _LOGGER.info(
            'juhe signature success, sporder_id:%s, order_no:%s', sporder_id, order_no)
        order_id = order_no[:-8]
        item = AutoShipping.query.filter(
            AutoShipping.order_id == order_id).with_lockmode('update').first()
        if not item:
            _LOGGER.error(
                'juhe check_notify_sign, order not found, order_id:%s, status:%s', order_id, status)
            return
        if status == 1:
            # trade success
            item.status = 1
            success = True
            _LOGGER.info(
                'juhe check_notify_sign, order %s trade success', order_id)
        else:
            item.status = 2
            success = False
            _LOGGER.info(
                'juhe check_notify_sign, order %s trade fail', order_id)
        item.save()
        change_order(order_id, success)
    else:
        _LOGGER.error(
            'juhe signature not verified, sporder_id:%s, order_no:%s', sporder_id, order_no)
