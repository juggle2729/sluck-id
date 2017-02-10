# -*- coding: utf-8 -*-
import json
import base64
import logging

from luckyapi.model.order import OrderDetail, BuyRecordLite
from luckyapi.logic import receipt as receipt_handler

from luckycommon.cache import redis_cache
from luckycommon.model.receipt import SHIPPING_TYPE
from luckycommon.model.show import AnnounceShow

from luckycommon.order.model.order import *
from luckycommon.order.db import order as order_db
from luckycommon.account.db import account as account_db
from luckycommon.db import activity as activity_db
from luckycommon.db import goods as goods_db
from luckycommon.db import show as show_db
from luckycommon.utils import id_generator
from luckycommon.utils.tz import utc_to_local
from luckycommon.utils.exceptions import ParamError, AuthenticateError

from django.conf import settings


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')

_DEFAULT_PAGE_SIZE = 10


def _create_order_lite_list(buy_orders, bind_uid=None):
    record_list = []
    for order in buy_orders:
        record_lite = BuyRecordLite()
        user = account_db.get_account(order.buyer, use_cache=True)
        geo_info = {} if not order.extend else json.loads(order.extend) or {}
        record_lite.uid = user.id
        record_lite.avatar = user.avatar_id
        record_lite.nick_name = user.nick_name
        record_lite.ip = geo_info.get('ip')
        record_lite.addr = geo_info.get('addr') or u'未知'
        record_lite.num_count = order.goods_quantity
        if not bind_uid:
            record_lite.numbers = []
        else:
            if not order.lucky_numbers:
                numbers = order_db.get_order_numbers(order.id)
                numbers = numbers[:20]
            else:
                numbers = order.lucky_numbers.split(',')[:20]
            record_lite.numbers = numbers
        record_lite.time = order.pay_at.split('.')[0]
        record_lite.order_id = order.id
        record_lite.order_id_str = str(order.id)
        record_list.append(record_lite)
    return record_list


def view_buy_record_list(user_id, page, size, activity_id,
                         for_admin=False, old_version=True):
    record_list = []
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    if user_id:
        if page > 1:
            return [], 0
        limit = 0
    offset = 0 if not page else (page - 1) * limit
    # check cache
    use_cache = False
    revealed = redis_cache.get_revealed(activity_id)
    if revealed:
        use_cache = True
    if use_cache:
        record_list = redis_cache.get_buy_records(user_id, activity_id, offset, limit)
    if not record_list:
        buy_orders, count = order_db.get_activity_orders(
            activity_id, user_id, limit, offset)
        record_list = _create_order_lite_list(buy_orders, user_id)
        if use_cache:
            redis_cache.set_buy_records(user_id, activity_id, offset, limit, record_list)

    return record_list, len(record_list)


def view_buy_record_list_timeline(activity_id, start_ts, max_ts):
    buy_orders = order_db.get_activity_orders_timeline(
        activity_id, start_ts, max_ts)
    return _create_order_lite_list(buy_orders)


def view_detail_numbers(order_id):
    order = order_db.get_order(order_id)
    if not order.lucky_numbers:
        return order_db.get_order_numbers(order.id)
    else:
        return order.lucky_numbers.split(',')


def update_award_order(user_id, order_id, receipt_info):
    """
    领奖, 提交收货地址
    """
    order = order_db.get_awarded_order(order_id)
    if order.user_id != user_id:
        raise AuthenticateError('no authentication to modify others order')
    if order.status != ORDER_STATUS.AWARDED:
        raise ParamError('order status invalid')

    receipt_id = receipt_info.get('id')
    shipping_type = int(receipt_info.get('shipping_type', 0))
    remark = receipt_info.get('remark')
    if remark:
        remark = remark.strip()
        remark = remark[:100]
    if not receipt_id:
        receipt_item = None
    else:
        receipt_item = receipt_handler.valid_receipt_address(
            user_id, receipt_id, shipping_type)
        if not receipt_item:
            raise ParamError('receipt id invalid')
        if shipping_type:
            receipt_info.update({
                'name': SHIPPING_TYPE.get_label(shipping_type),
                'phone': receipt_item.number,
                'address': ''
            })
        else:
            receipt_info.update({
                'shipping_type': shipping_type,
                'name': receipt_item.name,
                'phone': receipt_item.phone,
                'address': receipt_item.address,
                'addr_code': receipt_item.addr_code
            })
    if shipping_type:
        is_resell = receipt_info.get('is_resell')
        if not is_resell:
            receipt_info_new = {
                'shipping_type': shipping_type,
                'name': SHIPPING_TYPE.get_label(shipping_type),
                'phone': receipt_item.number if receipt_item else receipt_info.get(
                    'number'),
                'address': ''
            }
        else:
            receipt_info_new = {
                'shipping_type': shipping_type,
                'name': SHIPPING_TYPE.get_label(shipping_type),
                'resell_phone': receipt_info.get('resell_phone'),
                'resell_cabang': receipt_info.get('resell_cabang'),
                'resell_bank': receipt_info.get('resell_bank'),
                'resell_rekening': receipt_info.get('resell_rekening'),
                'resell_name': receipt_info.get('resell_name'),
                'address': ''
            }
        if shipping_type == 4:
            receipt_info_new.update({'address': receipt_info.get('email')})
        elif shipping_type == 5:
            receipt_info_new.update({'address': receipt_info.get('gojek')})
        elif shipping_type == 6:
            receipt_info_new.update({'address': receipt_info.get('electricity_bill')})
        receipt_info = receipt_info_new
    order_db.update_receipt_info(order_id, receipt_info, remark)
    redis_cache.remove_user_pending(user_id, 'award')


def show_order(order):
    """
    生成晒单
    order: <AwardedOrder>
    """
    activity = activity_db.get_activity(order.activity_id, need_fill=False)
    if activity.template_id not in settings.SHOW_BANNED_TIDS:
        show = show_db.create_show(activity.template_id, activity.term_number,
                                   order.order_id, order.user_id)
        AnnounceShow.start_notify_timer(show.id)


def affirm_receipt_order(user_id, order_id):
    """
    确认收货
    """
    order = order_db.get_awarded_order(order_id)
    if order.user_id != user_id:
        raise AuthenticateError('no authentication to modify others order')
    if order.status < ORDER_STATUS.WAIT_SHIP:
        raise ParamError('order not awarded')

    order_db.receipt_order(order_id)
    show_order(order)


def view_current_status(user_id, activity_id, order_id):
    order = order_db.get_awarded_order(order_id)
    if not order or order.activity_id != activity_id:
        raise ParamError('order id invalid')
    if order.user_id != user_id:
        raise AuthenticateError('no authentication to access others order')
    order_detail = OrderDetail()
    order_detail.order_id = order_id
    order_detail.activity_id = activity_id
    order_detail.uid = user_id
    order_detail.status = order.status
    extend = {} if not order.extend else json.loads(order.extend)
    if order.status >= ORDER_STATUS.AWARDED:
        activity = activity_db.get_activity(activity_id, need_fill=False)
        refer_goods = goods_db.get_goods(activity.goods_id)
        order_detail.shipping_type = refer_goods.shipping_type
        if order.shipping_coin:
            order_detail.shipping_type = SHIPPING_TYPE.COIN
    receipt_address = {} if not order.receipt_address else json.loads(
        order.receipt_address)
    if order.status in (ORDER_STATUS.WAIT_SHIP, ORDER_STATUS.WAIT_RECEIPT, ORDER_STATUS.DEAL, ORDER_STATUS.SHOW):
        # shipping_type = receipt_address.get('shipping_type')
        order_detail.receipt_info = {
            'name': receipt_address.get('name'),
            'phone': receipt_address.get('phone'),
            'number': receipt_address.get('phone'),  # for compatible
            'address': receipt_address.get('address'),
            'addr_code': receipt_address.get('addr_code')
        }
        if 'remark' in extend:
            order_detail.remark = extend.get('remark')
    if order.status in (ORDER_STATUS.WAIT_RECEIPT, ORDER_STATUS.DEAL, ORDER_STATUS.SHOW):
        express_name = extend.get('express')
        if express_name == 'coupon':
            express_name = None
            express_num = None
        else:
            express_num = extend.get('express_num')
        order_detail.shipping = {
            'express': express_name or '',
            'express_num': express_num or ''
        }
    if order.status in (ORDER_STATUS.DEAL, ORDER_STATUS.SHOW):
        try:
            order_show = show_db.get_show_by_order(order_id)
            order_detail.show_id = order_show.id
        except:
            pass
    if order.status in (ORDER_STATUS.PROCESSING, ORDER_STATUS.WAIT_AFFIRM, ORDER_STATUS.AFFIRMED):
        order_detail.receipt_info = receipt_address
        if 'remark' in extend:
            order_detail.remark = extend.get('remark')
    return order_detail


def view_order_detail(user_id, order_id):
    """
    deprecated
    """
    order = order_db.get_order(order_id)
    if order.buyer != user_id:
        raise AuthenticateError('no authentication to access others order')
    order_detail = OrderDetail()
    order_detail.order_id = order_id
    order_detail.activity_id = order.activity_id
    order_detail.quantity = order.goods_quantity
    order_detail.price = order.total_price
    order_detail.uid = user_id
    geo_info = {} if not order.extend else json.loads(order.extend)
    order_detail.ip = geo_info.get('ip')
    order_detail.addr = geo_info.get('addr') or u'未知'
    if not order.lucky_numbers:
        numbers = order_db.get_order_numbers(order.id)
    else:
        numbers = order.lucky_numbers.split(',')
    order_detail.numbers = numbers
    order_detail.status = order.status
    order_detail.time = order.pay_at.split('.')[0]
    order_detail.receipt_info = order.receipt_address
    return order_detail


def view_available_red_envelopes(user_id):
    r_list = []
    items = order_db.get_available_red_envelopes(user_id)
    for item in items:
        order_id = item.order_id
        order = order_db.get_awarded_order(order_id)
        if order.user_id != user_id:
            _LOGGER.warn('view available red, uid invalid, %s != %s', order.user_id, user_id)
            continue
        code = id_generator.generate_uuid(str(order_id) + str(user_id))
        activity_id = order.activity_id
        activity = activity_db.get_activity(activity_id, need_fill=False)
        r_list.append({
            'activity_id': activity_id,
            'activity_name': activity.name,
            'gid': activity.template_id,
            'term_number': activity.term_number,
            'cover': activity.cover,
            'code': base64.b64encode(code),
            'announce_time': utc_to_local(order.created_at).strftime('%Y-%m-%d %H:%M:%S'),
        })
    return r_list
