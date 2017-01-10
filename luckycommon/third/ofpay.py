# -*- coding: utf-8 -*-
import hashlib
import json
import logging
from time import strftime

import requests
import xmltodict

from luckycommon.model.shipping import AutoShipping
from luckycommon.model.receipt import SHIPPING_TYPE

from luckycommon.order.db import order as order_db
from luckycommon.order.model.order import ORDER_STATUS, SHIP_STATUS
from luckycommon.push import handler as push_handler
from luckyplatform.settings import OFFPAY_NOTIFY_URL

_LOGGER = logging.getLogger('ofpay')
_TRACKER = logging.getLogger('tracker')

RECHARGE_ENDPOINT = 'http://AXXXX.api2.ofpay.com/onlineorder.do'
USER_ID = 'A1322304'
USER_PASSWORD = 'Zhuohan2016'
KEY = 'OFCARD'
TELE_CARD_ID = '140101'  # 快充
QQ_CARD_ID = '220612'  # QQ 币, 面值 1 元
ALI_CARD_ID = '6102800'  # 支付宝直充
CHARGE_DICT = {
    'QQ': QQ_CARD_ID,
    'TELE': TELE_CARD_ID,
    'ALI': ALI_CARD_ID,
}
CALLBACK_URL = OFFPAY_NOTIFY_URL
VERSION = '6.0'


def _generate_sign(payload):
    raw_str = "%s%s%s%s%s%s%s%s" % (payload['userid'],
                                    payload['userpws'],
                                    payload['cardid'],
                                    payload['cardnum'],
                                    payload['sporder_id'],
                                    payload['sporder_time'],
                                    payload['game_userid'],
                                    KEY,
                                    )
    return hashlib.md5(raw_str).hexdigest().upper()


def tele_charge(order_id, template_id, user_id, phone, price):
    return charge('TELE', order_id, template_id, user_id, phone, price)


def qq_charge(order_id, template_id, user_id, phone, price):
    return charge('QQ', order_id, template_id, user_id, phone, price)


def ali_charge(order_id, template_id, user_id, phone, price):
    return charge('ALI', order_id, template_id, user_id, phone, price)


def charge(charge_type, order_id, template_id, user_id, phone, price):
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
        if charge_type == 'QQ':
            item.shipping_type = SHIPPING_TYPE.QQ
    else:
        return 2 if item.status == 2 else -1
    item.save()
    if charge_type == 'TELE' and phone.startswith('86'):
        phone_no = phone[2:]
    else:
        phone_no = phone
    payload = {
        'userid': USER_ID,
        'userpws': hashlib.md5(USER_PASSWORD).hexdigest().lower(),
        'cardid': CHARGE_DICT[charge_type],
        'cardnum': price if charge_type != 'ALI' else 1,
        'sporder_id': str(order_id) + 'sep' + str(user_id),
        'sporder_time': strftime("%Y%m%d%H%M%S"),
        'game_userid': phone_no,
        'ret_url': CALLBACK_URL,
        'version': VERSION,
    }
    if charge_type == 'ALI':
        payload['actprice'] = '{0:.1f}'.format(price)
    try:
        payload['md5_str'] = _generate_sign(payload)
        r = requests.get(RECHARGE_ENDPOINT, payload)
        item = AutoShipping.query.filter(
            AutoShipping.order_id == order_id).with_lockmode('update').first()
        item.response = r.text
        response_obj = xmltodict.parse(r.text)
        error_code = int(response_obj['orderinfo']['retcode'])
        if error_code != 1:
            item.status = 2
            _LOGGER.error('request recharge response error, %s', r.text)
    except Exception as e:
        item.status = 2
        _LOGGER.exception('requests recharge fail, %s', e)
    item.save()
    return item.status


def change_order(order_id, success, shipping_type):
    if success:
        # update order
        order_db.update_order_by_id(
            order_id,
            {
                'status': ORDER_STATUS.WAIT_RECEIPT,
                'ship_status': SHIP_STATUS.NORMAL
            })
        # push shipping
        if shipping_type == SHIPPING_TYPE.QQ:
            push_handler.push_shipping(order_id, {'express': 'qq'})
        else:
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
    return True


def check_notify_sign(request):
    # TODO: async job to do this
    sporder_id = request.POST.get('sporder_id')
    order_id, user_id = sporder_id.split('sep')
    status = int(request.POST.get('ret_code'))
    item = AutoShipping.query.filter(
        AutoShipping.order_id == order_id).with_lockmode('update').first()
    if not item:
        _LOGGER.error(
            'ofpay check_notify_sign, order not found, order_id:%s, status:%s', order_id, status)
        return
    if item.status != 0:
        _LOGGER.error(
            'ofpay check_notify_sign, order has been checked, order_id:%s, status:%s', order_id, item.status)
        return
    r = requests.get(
        'http://AXXXX.api2.ofpay.com/api/query.do?userid=%s&spbillid=%s' % (USER_ID, sporder_id))
    if status == 1 and int(r.text) == 1:
        # trade success
        item.status = 1
        success = True
        _LOGGER.info(
            'ofpay check_notify_sign, order %s trade success', order_id)
    else:
        item.status = 2
        success = False
        _LOGGER.info('ofpay check_notify_sign, order %s trade fail', order_id)
    item.save()
    change_order(order_id, success, item.shipping_type)


def manual_check(order_id ,user_id):
    sporder_id = str(order_id) + 'sep' + str(user_id)
    item = AutoShipping.query.filter(
        AutoShipping.order_id == order_id).first()
    if not item:
        _LOGGER.error(
            'ofpay manual_check, order not found, order_id:%s', order_id)
        return -1
    if item.status != 0:
        _LOGGER.error(
            'ofpay manual_check, order has been checked, order_id:%s, status:%s', order_id, item.status)
        return -1
    status = 0
    r = requests.get(
        'http://AXXXX.api2.ofpay.com/api/query.do?userid=%s&spbillid=%s' % (USER_ID, sporder_id))
    if int(r.text) == 1:
        # trade success
        item.status = 1
        success = True
        _LOGGER.info(
            'ofpay manual_check, order %s trade success', order_id)
        status = 1
    elif int(r.text) == 9:
        # trade fail
        item.status = 2
        success = False
        _LOGGER.info('ofpay manual_check, order %s trade fail', order_id)
        status = 2
    else:
        _LOGGER.info('ofpay manual_check, order %s in trade', order_id)

    if status != 0:
        item.save()
        change_order(order_id, success, item.shipping_type)
    return status


if __name__ == '__main__':
    # tele_charge('123252322', '23253ge', '323', '8615623099215', 20)
    qq_charge('123252322sep2323', '23253ge', '323', '82374617', 3)
