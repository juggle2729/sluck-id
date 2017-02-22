# -*- coding: utf-8 -*-
import json
import logging
from hashlib import md5
from datetime import datetime

from django.conf import settings

from luckycommon.order.model import orm
from luckycommon.order.model.order import *

from luckycommon.model.stock import Goods, SHIPPING_TYPE
from luckycommon.account.model.account import Account
from luckycommon.account.db.account import get_account
from luckycommon.model.activity import *
from luckycommon.model.transaction import *

from luckycommon.db.goods import get_goods
from luckycommon.db.activity import get_activity
from luckycommon.db.helper import (get_orderby, parse_query_dct,
                                   paginate, generate_filter)
from luckycommon.cache import redis_cache

from luckycommon.utils.types import Enum
from luckycommon.utils import id_generator
from luckycommon.utils.tz import utc_to_local, local_now, adjust_ts
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.exceptions import (DbError, ParamError,
                                          ResourceInsufficient,
                                          BalanceInsufficient,
                                          ResourceNotFound,
                                          ClientError, ServerError)
from luckycommon.utils.orm import get_count
from luckycommon.third.jd.order import submit_order

from future.utils import raise_with_traceback
from django.utils.translation import ugettext as _


_LOGGER = logging.getLogger('lucky')

_ANNOUNCE_CONDITION = 100


def _get_jd_ids(source):
    sources = source.split(',')
    ids = []
    for source in sources:
        if 'jd.com' not in source:
            continue
        source = source.split('/')
        source_id = source[-1] if '.' in source[-1] else source[-2]
        source_id = source_id.split('.')[0]
        ids.append(int(source_id))
    return ids


def _combine_jd_params(order):
    activity = get_activity(order.activity_id)
    if not activity:
        _LOGGER.error('activity not exist! orderid: %s', order.order_id)
    goods = get_goods(activity.goods_id)
    if not goods:
        _LOGGER.error('goods not exist! orderid:%s', order.order_id)
    if not goods.source or 'jd.com' not in goods.source:
        return {}, []
    source_ids = _get_jd_ids(goods.source)
    if order.receipt_address and order.receipt_address.startswith('{'):
        receipt_address = json.loads(order.receipt_address)
    else:
        receipt_address = {}
    addr_code = receipt_address.get('addr_code')
    if not addr_code:
        _LOGGER.error('no addr_code in receipt_address, order_id:%s',
                      order.order_id)
        return {}, []
    addr_code = json.loads(addr_code)
    params = {
        "thirdOrder": str(order.order_id),
        "sku": [{'id': source_ids[0], 'num': goods.num}],
        "name": receipt_address.get('name'),
        "province": addr_code[0].get('id'),
        "city": addr_code[1].get('id'),
        "county": addr_code[2].get('id'),
        "town": addr_code[3].get('id') if len(addr_code) == 4 else 0,
        "address": receipt_address.get('address'),
        "zip": 100000,
        "mobile": receipt_address.get('phone'),
        "email": "mytian@adsquare-tech.com",
        "invoiceState": 2,
        "invoiceType": 2,
        "selectedInvoiceTitle": 5,
        "companyName": u"武汉卓翰网络科技有限公司",
        "invoiceContent": 1,
        "paymentType": 4,
        "isUseBalance": 1,
        "submitState": 1,
    }
    return params, source_ids


def send_order(order_id):
    order = AwardedOrder.query.with_for_update().filter(
        AwardedOrder.order_id == order_id).one()
    if order.status != ORDER_STATUS.WAIT_SHIP:
        return False
    params, source_ids = _combine_jd_params(order)
    extend = json.loads(order.extend or '{}')
    for source_id in source_ids:
        params['sku'][0]['id'] = source_id
        resp = submit_order(params)
        if resp['success'] is True:
            order.status = ORDER_STATUS.WAIT_RECEIPT
            extend['express'] = u'京东'
            extend['express_num'] = resp['jdOrderId']
            extend['send_time'] = local_now().strftime('%Y-%m-%d %H:%M:%S')
            extend['buy_price'] = resp['orderPrice']
            extend['buy_from'] = u'京东'
            order.extend = json.dumps(extend, ensure_ascii=False)
            order.save()
            return True
        else:
            order.ship_status = SHIP_STATUS.SHIPPING_FAILED
            extend['ship_msg'] = resp['msg']
            order.extend = json.dumps(extend, ensure_ascii=False)
            order.save()
            if resp['code'] == '3008':  # 库存不足
                continue
            return False
    return False


@sql_wrapper
def get_order(order_id):
    order = Order.query.filter(Order.id == order_id).first()
    if not order:
        raise_with_traceback(
            ResourceNotFound("order %s not exists" % order_id))
    return order


@sql_wrapper
def get_awarded_order(order_id):
    order = AwardedOrder.query.filter(
        AwardedOrder.order_id == order_id).first()
    return order


@sql_wrapper
def get_order_numbers(order_id):
    item = OrderNumber.query.filter(OrderNumber.order_id == order_id).one()
    return item.numbers.split(',')


@sql_wrapper
def list_orders(query_dct, nonvirtual=False):
    id_filter = query_dct.pop('id', None)
    if id_filter is not None:
        order_id = long(id_filter)
        item = get_awarded_order(order_id)
        if not item:
            item = get_order(order_id)
            buyer = item.buyer
            award_only = False
        else:
            buyer = item.user_id
            award_only = True
        is_virtual = redis_cache.is_virtual_account(buyer)
        return [(item, is_virtual)], 1, award_only
    name_filter = query_dct.pop('activity_name', None)
    type_filter = query_dct.pop('activity_type', None)
    status_filter = query_dct.get('status')
    table = Order
    user_field = "buyer"
    award_only = False
    if (status_filter and int(status_filter) >= ORDER_STATUS.AWARDED) or\
            'extend' in query_dct:
        table = AwardedOrder
        user_field = "user_id"
        if 'buyer' in query_dct:
            query_dct['user_id'] = query_dct.pop('buyer')
        award_only = True
    query_dct = parse_query_dct(query_dct, table)
    query = orm.session.query(table, Account.is_virtual).join(
        Account, getattr(table, user_field) == Account.id)
    if name_filter or type_filter:
        query = query.join(Activity, table.activity_id == Activity.id)
        if name_filter:
            query = query.filter(Activity.name.like("%%%s%%" % name_filter))
        if type_filter:
            t = int(type_filter)
            if t == 0:
                query = query.filter(Activity.price == 0)
            else:
                query = query.filter(Activity.unit == t)
    # only non-virtual
    if nonvirtual:
        query = query.filter(Account.is_virtual == False)
    query = query.filter(generate_filter(query_dct, table))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), table)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)
    return query.all(), total_count, award_only


def _special_filter_awarded(query_dct):
    name_filter = query_dct.pop('activity_name', None)
    user_filter = query_dct.pop('buyer', None)
    query_dct.pop('express', None)
    query = AwardedOrder.query
    if user_filter is not None:
        query = query.filter(AwardedOrder.user_id == long(user_filter))
    else:
        query = query.join(
            Account, Account.id == AwardedOrder.user_id).filter(
            Account.is_virtual == False)
    if name_filter is not None:
        query = query.join(
            Activity, Activity.id == AwardedOrder.activity_id).filter(
            Activity.name.like("%%%s%%" % name_filter))
    query_dct = parse_query_dct(query_dct, AwardedOrder)
    query = query.filter(generate_filter(query_dct, AwardedOrder))
    return query


@sql_wrapper
def export_sent_orders(query_dct):
    query = _special_filter_awarded(query_dct)
    items = query.all()
    resp_items = []

    for item in items:
        activity = Activity.query.filter(
            Activity.id == item.activity_id).first()
        if not activity:
            continue
        extend = json.loads(item.extend or '{}')
        if not extend.get('express'):
            continue
        data = [utc_to_local(item.updated_at).strftime('%Y-%m-%d'),
                item.order_id, item.user_id, activity.name,
                extend.get('express', ''),
                extend.get('express_num', ''),
                extend.get('buy_from', ''),
                extend.get('buy_price', '')]
        resp_items.append(data)

    return resp_items


def batch_ship_orders(data, by=None):
    if not data:
        return
    ship_push = []
    for order_id, express_num, express, buy_from, buy_price in data:
        try:
            order_id = long(order_id)
        except ValueError:
            continue
        order = AwardedOrder.query.with_for_update().filter(
            AwardedOrder.order_id == long(order_id)).first()
        if not order:
            _LOGGER.error("FAIL to find %s to update status", order_id)
            continue
        if order.status != ORDER_STATUS.WAIT_SHIP:
            _LOGGER.error("order %s status is %s, skip",
                          order_id, order.status)
            continue
        order.status = ORDER_STATUS.WAIT_RECEIPT
        order.ship_status = SHIP_STATUS.NORMAL
        extend = json.loads(order.extend or '{}')
        extend['express_num'] = str(express_num).strip()
        extend['express'] = express.strip() or u'京东'
        extend['buy_from'] = buy_from.strip()
        extend['buy_price'] = float(buy_price)
        extend['send_time'] = local_now().strftime('%Y-%m-%d %H:%M:%S')
        if by:
            extend['send_by'] = by
        order.extend = json.dumps(extend, ensure_ascii=False)
        order.save()
        _LOGGER.info('sent order %s by %s', order_id, by)
        ship_push.append([order_id, extend])
    return ship_push


@sql_wrapper
def export_awarded_orders(query_dct):
    query = _special_filter_awarded(query_dct)
    ship_status = query_dct.get('ship_status')
    items = query.all()
    resp_items = []
    for item in items:
        activity = Activity.query.filter(
            Activity.id == item.activity_id).first()
        if not activity:
            continue
        goods = Goods.query.filter(Goods.id == activity.goods_id).first()
        if not goods:
            continue
        # default no virtual goods type
        #if not ship_status and goods.shipping_type != 0:
        #    continue
        if goods.source and 'jd.com' in goods.source:
            try:
                source_id = _get_jd_ids(goods.source)[0]
            except ValueError:
                _LOGGER.error('source_id get error: %s', goods.source)
                source_id = ''
        else:
            source_id = ''

        try:
            addr = json.loads(item.receipt_address or '{}')
            data = [str(item.order_id) + ' ', item.user_id, addr.get('name')]
            addr_list = []
            if addr.get('addr_code'):
                addr_code = json.loads(addr['addr_code'])  # 直辖市
                if addr_code and addr_code[0]['name'].endswith(u'市'):
                    addr_list.append('')
                for k in addr_code:
                    addr_list.append(k['name'])
            else:
                addr_list = addr.get('address', '').split(' ')
                if addr_list and addr_list[0].endswith(u'市'):
                    addr_list = [''] + addr_list
                addr['address'] = ''.join(addr_list[4:])
                addr_list = addr_list[:4]
        except (ValueError, TypeError):
            continue
        if len(addr_list) < 4:
            pad_list = (4 - len(addr_list)) * ['']
            addr_list += pad_list
        elif len(addr_list) > 4:
            addr_list = addr_list[:4]
        data += addr_list
        data += [addr.get('address'), addr.get('phone'),
                 source_id, goods.source_name or goods.name]
        data.append(item.remark or '')
        resp_items.append(data)
    return resp_items


@sql_wrapper
def get_activity_orders(activity_id, buyer=None, limit=0, offset=0,
                        order_by=None, desc=False):
    query = Order.query.filter(Order.activity_id == activity_id)
    if buyer:
        query = query.filter(Order.buyer == buyer)
    query = query.order_by(Order.pay_at.desc())
    #count = get_count(query)
    if limit > 0:
        query = query.limit(limit)
        query = query.offset(offset)
    items = query.all()
    return items, len(items)


_TIMELINE_SIZE = 10


@sql_wrapper
def get_activity_orders_timeline(activity_id, start_ts, max_ts=-1,
                                 limit=_TIMELINE_SIZE):
    """
    timeline实现方式
    """
    query = Order.query.filter(Order.activity_id == activity_id)
    query = query.filter(Order.id > start_ts)
    if max_ts != -1:
        query = query.filter(Order.id < max_ts)
    query = query.order_by(Order.id.desc())
    if limit > 0:
        query = query.limit(limit)
    return query.all()


@sql_wrapper
def get_user_orders(buyer, only_win, limit=0, offset=0,
                    order_by=None, desc=False):
    query = Order.query.filter(Order.buyer == buyer)
    if only_win:
        query = query.filter(Order.status >= ORDER_STATUS.AWARDED)
    if order_by and hasattr(Order, order_by):
        if desc:
            query = query.order_by(getattr(Order, order_by).desc())
        else:
            query = query.order_by(getattr(Order, order_by))
    total_count = get_count(query)
    if limit > 0:
        query = query.limit(limit)
        query = query.offset(offset)
    return query.all(), total_count


@sql_wrapper
def get_last_valid_orders(last_payat=None, num=_ANNOUNCE_CONDITION):
    if last_payat:
        query = Order.query.filter(
            Order.pay_at <= last_payat).order_by(Order.pay_at.desc())
    else:
        query = Order.query.order_by(Order.pay_at.desc())
    query = query.offset(0).limit(num)
    return query.all()


@sql_wrapper
def get_orders_by_time(start_time, end_time, limit, offset):
    query = Order.query.filter(orm.and_(Order.pay_at >= start_time,
                                        Order.pay_at <= end_time))
    total_count = get_count(query)
    query = query.order_by(Order.pay_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    return query.all(), total_count


@sql_wrapper
def update_receipt_info(order_id, receipt_info, remark=None, origin_info=None):
    order = AwardedOrder.query.filter(
        AwardedOrder.order_id == order_id).first()
    receipt_addr = json.dumps(receipt_info, ensure_ascii=False)
    order.receipt_address = receipt_addr
    order.status = ORDER_STATUS.PROCESSING if 'resell_name' in receipt_info else ORDER_STATUS.WAIT_SHIP
    if remark:
        order.remark = remark
    extend = json.loads(order.extend or '{}')
    extend.update({
        'award_time': local_now().strftime('%Y-%m-%d %H:%M:%S')
    })
    extend.update({
        'origin': origin_info
    })
    order.extend = json.dumps(extend, ensure_ascii=False)
    if SHIPPING_TYPE.BALANCE == receipt_info.get('shipping_type'):
        order.shipping_coin = 1
    order.save()


SALT = 'aR%7#u'


def encoding_code(code):
    return md5(code + SALT).hexdigest()


@sql_wrapper
def get_red_envelope_info(code):
    red_envelope = RedEnvelope.query.filter(
        RedEnvelope.id == encoding_code(code)).first()
    if not red_envelope:
        return {}
    return red_envelope.as_dict()


@sql_wrapper
def get_available_red_envelopes(user_id):
    return RedEnvelope.query.filter(
        RedEnvelope.user_id == user_id).filter(
        RedEnvelope.status == 0).all()


@sql_wrapper
def sent_red_envelope_callback(order_no):
    order = AwardedOrder.query.with_for_update().filter(
        AwardedOrder.order_id == long(order_no)).one()
    if order.status != ORDER_STATUS.WAIT_SHIP or\
            order.ship_status != SHIP_STATUS.CHARGING:
        raise_with_traceback(ParamError(
            'fail to check status when callback sent envelope, order id:%s' %
            order_no))
    order.status = ORDER_STATUS.WAIT_RECEIPT
    order.ship_status = SHIP_STATUS.NORMAL
    extend = json.loads(order.extend or '{}')
    extend['send_time'] = local_now().strftime('%Y-%m-%d %H:%M:%S')
    order.extend = json.dumps(extend, ensure_ascii=False)
    order.save()


@sql_wrapper
def received_pingxx_callback(order_no):
    order = AwardedOrder.query.with_for_update().filter(
        AwardedOrder.order_id == long(order_no)).one()
    order.status = ORDER_STATUS.DEAL
    extend = json.loads(order.extend or '{}')
    extend['receive_time'] = local_now().strftime('%Y-%m-%d %H:%M:%S')
    order.extend = json.dumps(extend, ensure_ascii=False)
    order.save()


@sql_wrapper
def received_transfer_callback(order_no):
    order = AwardedOrder.query.with_for_update().filter(
        AwardedOrder.order_id == long(order_no)).one()
    if order.status != ORDER_STATUS.WAIT_SHIP:
        _LOGGER.error('fail to check transfer status, id: %s', order_no)
        return
    order.status = ORDER_STATUS.DEAL


@sql_wrapper
def update_order_info(order_id, info, by=None, admin=False):
    if info['status'] < ORDER_STATUS.WAIT_SHIP and not admin:
        raise ParamError('status invalid')
    order = AwardedOrder.query.with_for_update().filter(
        AwardedOrder.order_id == order_id).first()
    extend = info.get('extend') or '{}'
    exist_extend = json.loads(order.extend or '{}')
    exist_extend.update(json.loads(extend))
    extend = exist_extend

    need_shipping_push = need_receipt_push = False
    if (order and order.status == ORDER_STATUS.WAIT_SHIP and
            info['status'] == ORDER_STATUS.WAIT_RECEIPT):
        need_shipping_push = True
        extend['send_time'] = local_now().strftime('%Y-%m-%d %H:%M:%S')
        extend.pop('ship_msg', None)
        extend['send_by'] = by
        order.ship_status = SHIP_STATUS.NORMAL
    if (order and order.status == ORDER_STATUS.WAIT_RECEIPT and
            info['status'] == ORDER_STATUS.DEAL):
        need_receipt_push = True
        extend['receive_time'] = local_now().strftime('%Y-%m-%d %H:%M:%S')
    for k, v in info.iteritems():
        if hasattr(order, k) and k not in (
                'extend', 'updated_at', 'created_at'):
            setattr(order, k, v)
    order.extend = json.dumps(extend, ensure_ascii=False)
    order.save()
    return need_shipping_push, need_receipt_push


@sql_wrapper
def receipt_order(order_id):
    
    order = AwardedOrder.query.filter(
        AwardedOrder.order_id == order_id).first()
    if order.status == ORDER_STATUS.WAIT_AFFIRM:
        AwardedOrder.query.filter(AwardedOrder.order_id == order_id).update({
            'status': ORDER_STATUS.AFFIRMED,
            'updated_at': datetime.utcnow()
        })
    else:
        AwardedOrder.query.filter(AwardedOrder.order_id == order_id).update({
            'status': ORDER_STATUS.DEAL,
            'updated_at': datetime.utcnow()
        })
    # Order.query.filter(Order.id == order_id).update({
    #     'status': ORDER_STATUS.DEAL,
    #     'updated_at': datetime.utcnow()
    # })
    orm.session.commit()


@sql_wrapper
def get_order_routes(order_id):
    query = OrderRoute.query.filter(OrderRoute.order_id == order_id)
    query = query.order_by(OrderRoute.created_at)
    return query.all()


@sql_wrapper
def add_order_route(order_id, status, operator=None, content=None):
    order_route = OrderRoute()
    order_route.order_id = order_id
    order_route.status = status
    if status == ORDER_STATUS.AWARDED:
        order_route.content = u'恭喜您购物成功，请尽快填写收货地址，以便我们为您配送！'
        order_route.operator = u'一元购系统'
    if status == ORDER_STATUS.WAIT_SHIP:
        order_route.content = u'会员已填写配送信息，等待商城发货！'
        order_route.operator = u'会员本人'
    if status == ORDER_STATUS.DEAL:
        order_route.content = u'已成功提交确认收货！'
        order_route.operator = u'会员本人'
    order_route.save()


class OrderPayer:

    """
    Provide class method to pay order,
    hide some private method for database transaction.
    """
    _MAX_TRY = 1

    PAY_STATUS = Enum({
        "SUCCESS": (0L, "pay success"),
        "BALANCE_ERROR": (1L, "balance insufficient"),
        "COCURRENCY_ERROR": (2L, "cocurrency error")
    })

    @classmethod
    def __create_order(cls, order_record, need_adjust):
        """
        we shouldn't add try/except here,
        any exception must be raised outside
        """
        order = Order()
        # order.id = id_generator.generate_long_id('order')
        order.status = ORDER_STATUS.PAYED
        order.activity_id = order_record.activity_id
        order.goods_quantity = order_record.quantity
        order.total_price = order_record.price
        order.buyer = order_record.user_id
        # order.lucky_numbers = ','.join(order_record.lucky_numbers)
        # for performance
        order.lucky_numbers = None
        order.extend = json.dumps(order_record.extend, ensure_ascii=False)
        dt = utc_to_local(datetime.utcnow())
        if need_adjust:
            dt = adjust_ts(dt, delta_seconds=3)
        order.pay_at = dt.strftime(
            '%Y-%m-%d %H:%M:%S.') + dt.strftime('%f')[:3]
        order.save(auto_commit=False)

        return order

    @classmethod
    def __create_order_number(cls, order_id, order_record):
        order_number = OrderNumber()
        order_number.order_id = order_id
        order_number.numbers = ','.join(order_record.lucky_numbers)
        order_number.save(auto_commit=False)

    @classmethod
    def __create_pay_bill(cls, account, order):
        """
        we shouldn't add try/except here,
        any exception must be raised outside
        """
        transaction = Transaction()
        transaction.id = id_generator.generate_long_id('transaction')
        transaction.user_id = account.id
        transaction.type = TRANSACTION_TYPE.BALANCE_BUY
        transaction.title = u"Đơn thanh toán"
        transaction.price = -order.total_price
        transaction.balance = account.balance - order.total_price
        transaction.order_id = order.id
        transaction.status = TRANSACTION_STATUS.DONE
        transaction.save(auto_commit=False)

        return transaction.id

    @classmethod
    def __index_user_activity(cls, user_id, activity_id, numbers, buy_limit):
        user_activity = UserActivity.query.filter(UserActivity.user_id == user_id)\
            .filter(UserActivity.activity_id == activity_id)\
            .with_lockmode('update').first()
        if not user_activity:
            user_activity = UserActivity()
            user_activity.user_id = user_id
            user_activity.activity_id = activity_id
            user_activity.numbers = ','.join(numbers)
            user_activity.save(auto_commit=False)
            orm.session.flush()
            _LOGGER.info('create user activity success: %s' % user_activity.id)
            redis_cache.add_top_buyer(activity_id, user_id, len(numbers))
        else:
            old_numbers = [] if not user_activity.numbers else user_activity.numbers.split(
                ',')
            if buy_limit:
                if len(old_numbers) + len(numbers) > buy_limit:
                    raise ResourceInsufficient(
                        "buy limit (%s) reached." % buy_limit)
            old_numbers.extend(numbers)
            user_activity.numbers = ','.join(old_numbers)
            user_activity.save(auto_commit=False)
            redis_cache.add_top_buyer(activity_id, user_id, len(old_numbers))

    @classmethod
    def pay(cls, order_record, buy_limit, need_adjust):
        try_count = 1

        while try_count <= cls._MAX_TRY:
            try:
                account = get_account(order_record.user_id)
                old_balance = account.balance
                new_balance = old_balance - order_record.price
                if new_balance < 0:
                    raise BalanceInsufficient("account balance insufficient")

                # database transaction operation
                # 1.debit balance --> 2.create bill --> 3.pay order
                res = Account.query.filter(Account.id == order_record.user_id).filter(
                    Account.balance == old_balance).update({'balance': new_balance})
                if not res:
                    _LOGGER.warn(
                        'coucurrency trouble when debit account, try count(%d)' % try_count)
                    raise
                else:
                    # do transaction
                    order = cls.__create_order(order_record, need_adjust)
                    orm.session.flush()
                    cls.__create_order_number(order.id, order_record)
                    bill_id = cls.__create_pay_bill(account, order)
                    cls.__index_user_activity(order.buyer, order.activity_id,
                        order_record.lucky_numbers, buy_limit)
                    orm.session.commit()
                    _LOGGER.info(
                        '%s pay order[%s] success' % (order.buyer, order.id))

                    return order
            except Exception as e:
                try_count += 1
                orm.session.rollback()
                _LOGGER.exception(
                    'account debit transaction operation exception.(%s)' % e)
            finally:
                orm.session.close()

        if try_count > cls._MAX_TRY:
            raise DbError("cocurrency trouble when pay order")


class Refunder:

    """
    Provide class method to refunding
    """
    @classmethod
    def __refund_account(cls, user_id, price):
        account = Account.query.filter(
            Account.id == user_id).with_lockmode('update').first()
        account.balance = account.balance + price

    @classmethod
    def __refund_transaction(cls, order, account):
        transaction = Transaction()
        transaction.id = id_generator.generate_long_id('transaction')
        transaction.user_id = order.buyer
        transaction.type = TRANSACTION_TYPE.REFUND
        transaction.title = u"Đơn trả lại tiền"
        transaction.price = order.total_price
        transaction.balance = account.balance
        transaction.order_id = order.id
        transaction.status = TRANSACTION_STATUS.DONE
        transaction.save(auto_commit=False)

    @classmethod
    def refund(cls, activity_id):
        orders, count = get_activity_orders(activity_id)
        refunded_count = 0
        refunded_users = {}
        for order in orders:
            try:
                # do transaction
                # 1. add balance to account --> 2. add transaction record
                account = cls.__refund_account(order.buyer, order.total_price)
                cls.__refund_transaction(order, account)
                orm.session.commit()
                refunded_count += 1
                refunded_users.setdefault(order.buyer, 0)
                refunded_users[order.buyer] += order.total_price
                _LOGGER.info('refund order[%s] success' % order.id)
            except Exception as e:
                orm.session.rollback()
                _LOGGER.error(
                    'refund order[%s] exception.(%s)' % (order.id, e))
            finally:
                orm.session.close()

        _LOGGER.info('Refunder refund %s orders for activity[%s], total %s' %
                     (refunded_count, activity_id, count))
        return refunded_users
