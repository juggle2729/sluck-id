# -*- coding: utf-8 -*-

''' 控制台专用的一些接口
'''
import logging
import json

from dateutil import parser

from luckycommon.order.model.order import (Order, CombineAwardedOrder,
                                           ORDER_STATUS, SHIP_STATUS,
                                           AwardedOrder, Area)
from luckycommon.model.activity import Activity
from luckycommon.cache.redis_cache import is_virtual_account
from luckycommon.db.activity import get_activity
from luckycommon.model import orm, slave
from luckycommon.model.stock import Goods
from luckycommon.db.goods import (get_source, get_goods, get_brand,
                                  get_category_path)
from luckycommon.third.jd.order import submit_order
from luckycommon.model.account import Account
from luckycommon.utils.decorator import sql_wrapper, slave_wrapper
from luckycommon.order.db.order import update_order
from luckycommon.utils.api import dict2obj
from luckycommon.db.helper import (get_orderby, parse_query_dct,
                                   paginate, generate_filter, get_count)
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)


def _combine_order_activity_info(order_dct, activity):
    order_dct['activity_name'] = activity.name
    for k in 'goods_id', 'term_number', 'target_amount':
        order_dct[k] = getattr(activity, k)
    order_dct['goods_id'] = activity.goods_id


def _combine_order_goods_info(order_dct, goods):
    if goods:
        order_dct['goods_name'] = goods.name
        order_dct['goods_num'] = goods.num
        for k in ('shipping_type', 'source', 'source_type', 'source_name',
                  'category_id', 'brand_id', 'price'):
            order_dct[k] = getattr(goods, k)


@slave_wrapper
def get_order(order_id, as_dict=True):
    # only for console usage
    order = slave.session.query(CombineAwardedOrder).filter(
        CombineAwardedOrder.id == order_id).first()
    goods = None
    if not order:
        order = slave.session.query(Order).filter(Order.id == order_id).one()
        order = order.as_dict()
        activity = get_activity(order['activity_id'])
        _combine_order_activity_info(order, activity)
        extend = json.loads(order['extend'] or '{}')
        order.update(extend)
        goods = get_goods(activity.goods_id)
    else:
        goods = get_goods(order.goods_id)
        order = order.as_dict()

    _combine_order_goods_info(order, goods)
    for k in 'updated_at', 'created_at':
        order[k] = utc_to_local_str(order[k])

    order['id'] = str(order['id'])
    if not as_dict:
        return dict2obj(order)

    return order


def _convert_query_dct(query_dct):
    ''' for compatible reason
    '''
    if 'activity_name' in query_dct:
        query_dct['activity_name'] = json.dumps(
            {'$like': query_dct['activity_name']})
    return query_dct


@slave_wrapper
def list_awarded_orders(query_dct):
    query_dct = _convert_query_dct(query_dct)
    # goods_filter: goods_name, source_type, shipping_type
    query = slave.session.query(CombineAwardedOrder, Goods).join(
        Goods, CombineAwardedOrder.goods_id == Goods.id)
    for k in 'goods_name', 'source_type', 'shipping_type', 'brand_id':
        if k in query_dct:
            v = query_dct.pop(k)
            if k == 'goods_name':
                query = query.filter(Goods.name.like('%%%s%%' % v))
            else:
                query = query.filter(getattr(Goods, k) == int(v))
    query_dct = parse_query_dct(query_dct, CombineAwardedOrder)
    query = query.filter(generate_filter(query_dct, CombineAwardedOrder))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), CombineAwardedOrder)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)
    resp_items = []
    for item in query.all():
        order, goods = item
        data = order.as_dict()
        _combine_order_goods_info(data, goods)
        for k in 'updated_at', 'created_at':
            data[k] = utc_to_local_str(data[k])
        data['id'] = str(data['id'])
        resp_items.append(data)
    return resp_items, total_count


@slave_wrapper
def list_orders(query_dct):
    order_id = query_dct.pop('id', None)
    if order_id is not None:
        order = get_order(long(order_id))
        return order, 1
    if int(query_dct.get('status', 0)) >= ORDER_STATUS.AWARDED:
        return list_awarded_orders(query_dct)
    for k in ('express_num', 'buy_from', 'send_time', 'award_time',
              'ship_status', 'source_type'):
        if k in query_dct:
            return list_awarded_orders(query_dct)

    # 非中奖订单使用activity_name代替goods_name
    query = slave.session.query(Order, Activity).join(
        Activity, Activity.id == Order.activity_id)
    goods_name = query_dct.pop('goods_name', None)
    if goods_name is not None:
        query = query.filter(Activity.name.like('%%%s%%' % goods_name))
    query_dct = parse_query_dct(query_dct, Order)
    query = query.filter(generate_filter(query_dct, Order))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), Order)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)
    resp_items = []
    for item in query.all():
        order, activity = item
        data = order.as_dict()
        activity = get_activity(order.activity_id)
        _combine_order_activity_info(data, activity)
        goods = get_goods(activity.goods_id)
        _combine_order_goods_info(data, goods)
        data['is_virtual'] = is_virtual_account(order.buyer)
        data['id'] = str(data['id'])
        resp_items.append(data)
    return resp_items, total_count


@slave_wrapper
def list_order_stats(query_dct):
    # 统计信息专用
    name_filter = query_dct.pop('activity_name', None)
    if name_filter is None:
        name_filter = query_dct.pop('goods_name', None)
    type_filter = query_dct.pop('activity_type', None)
    query_dct = parse_query_dct(query_dct, Order)
    # only non-virtual
    query = slave.session.query(Order).join(
        Account, Order.buyer == Account.id).filter(
        Account.is_virtual == False)
    if name_filter or type_filter:
        query = query.join(Activity, Order.activity_id == Activity.id)
        if name_filter:
            query = query.filter(Activity.name.like("%%%s%%" % name_filter))
        if type_filter:
            t = int(type_filter)
            if t == 0:
                query = query.filter(Activity.price == 0)
            else:
                query = query.filter(Activity.unit == t)
    query = query.filter(generate_filter(query_dct, Order))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), Order)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)

    return query.all(), total_count


@sql_wrapper
def batch_ship_orders(data, by):
    if not data:
        return
    result = {
        'push': [],
        'succ': 0,
        'fail': 0
    }
    for item in data:
        order_id = item
        try:
            remark = ''
            if len(item) == 6:
                (order_id, express_num, express, buy_from, buy_price,
                    send_time) = item
            elif len(item) == 7:
                (order_id, express_num, express, buy_from, buy_price,
                    send_time, remark) = item
            order_id = long(order_id)
            order = AwardedOrder.query.with_for_update().filter(
                AwardedOrder.order_id == long(order_id)).one()
            assert order.status == ORDER_STATUS.WAIT_SHIP
            if isinstance(express_num, float):
                express_num = long(express_num)
            extend = {
                'express_num': str(express_num).strip(),
                'express': express.strip() or u'京东',
                'buy_from': buy_from,
                'buy_price': round(float(buy_price), 2),
                'send_time': parser.parse(send_time).strftime('%Y-%m-%d'),
                'remark': remark
            }
            info = {
                'status': ORDER_STATUS.WAIT_RECEIPT,
                'extend': json.dumps(extend, ensure_ascii=False)
            }
            update_order(order, info)
            result['push'].append([order_id, extend])
            result['succ'] += 1
        except Exception:
            _LOGGER.exception('send order error')
            result['fail'] += 1

    if result['succ'] == 0:
        result['fail'] = len(data)
    return result


def _combine_addrlist(addr):
    addr_list = []
    if addr.get('addr_code'):
        addr_code = json.loads(addr['addr_code'])  # 直辖市
        for k in addr_code:
            addr_list.append(k['name'])
    else:
        # 兼容旧版
        addr_list = addr.get('address', '').split(' ')
        if addr_list and addr_list[0].endswith(u'市'):
            addr_list = [''] + addr_list
        addr['address'] = ''.join(addr_list[4:])
        addr_list = addr_list[:4]

    if len(addr_list) < 4:
        pad_list = (4 - len(addr_list)) * ['']
        addr_list += pad_list
    elif len(addr_list) > 4:
        addr_list = addr_list[:4]
    return addr_list


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


def _get_sourceid(source):
    source_id = ''
    if source and 'jd.com' in source:
        try:
            source_id = _get_jd_ids(source)[0]
        except ValueError:
            pass

    return source_id


def export_orders(query_dct):
    items, _ = list_awarded_orders(query_dct)
    resp_items = []
    for item in items:
        try:
            addr = json.loads(item['receipt_address'] or '{}')
            data = [str(item['id']) + ' ', item['buyer'], addr.get('name')]
            addr_list = _combine_addrlist(addr)
        except (ValueError, TypeError):
            continue
        data += addr_list
        source_id = _get_sourceid(item['source'])
        if item['source_type']:
            source_type = get_source(item['source_type']).name
        else:
            source_type = '-'
        data += [addr.get('address'), addr.get('phone'), source_type,
                 source_id, item['source_name'] or item['goods_name'],
                 item['remark'] or '-',
                 item['award_time'] or '-']
        if item['status'] > ORDER_STATUS.WAIT_SHIP:
            brand_name = get_brand(
                item['brand_id']).name if item['brand_id'] else ''
            cas = get_category_path(item['category_id'])
            ca_names = []
            for ca in cas:
                ca_names.append(ca.name)
            data += [item['send_time'] or '-', brand_name,
                     item['buy_from'], '/'.join(ca_names),
                     item['price'] or '-', item['buy_price'] or '-',
                     item['express'] or '-', item['express_num'] or '-']
        else:
            data += ['-'] * 8

        resp_items.append(data)
    return resp_items


def _combine_jd_params(order):
    source_ids = _get_jd_ids(order.source)
    if order.receipt_address and order.receipt_address.startswith('{'):
        receipt_address = json.loads(order.receipt_address)
    else:
        receipt_address = {}
    addr_code = receipt_address.get('addr_code')
    if not addr_code:
        _LOGGER.error('no addr_code in receipt_address, order_id:%s',
                      order.id)
        return {}, []
    if order.ship_status >= SHIP_STATUS.ILLEGAL:
        _LOGGER.info('ignore illegal order')
        return {}, []
    addr_code = json.loads(addr_code)
    if not addr_code:
        _LOGGER.error('addr_code is empty, order_id:%s', order.id)
        return {}, []
    town = int(addr_code[3].get('id') or 0) if len(addr_code) == 4 else 0
    if town == 0 and "parent_id" in addr_code[2]:       # iOS地址bug
        town = orm.session.query(Area.id).filter(
            Area.parent_id == int(addr_code[2]['id'])).filter(
            Area.name == u'城区').scalar() or 0
    params = {
        "thirdOrder": str(order.id),
        "sku": [{'id': source_ids[0], 'num': order.goods_num}],
        "name": receipt_address.get('name'),
        "province": int(addr_code[0].get('id')),
        "city": int(addr_code[1].get('id')),
        "county": int(addr_code[2].get('id')),
        "town": town,
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


@sql_wrapper
def send_order(order_id, user_id):
    order_ex = get_order(order_id, as_dict=False)
    order = AwardedOrder.query.with_for_update().filter(
        AwardedOrder.order_id == order_id).one()
    if (order.status != ORDER_STATUS.WAIT_SHIP or
        order_ex.source_type != 6 or            # 6是京东慧采，注意这里写死了..
            order_ex.is_virtual):
        return False
    params, source_ids = _combine_jd_params(order_ex)
    extend = {}
    for source_id in source_ids:
        _LOGGER.debug('sending order %s, source_id: %s', order_id, source_id)
        params['sku'][0]['id'] = source_id
        resp = submit_order(params)
        if resp['success'] is True:
            extend = {
                'express': u'京东',
                'express_num': resp['jdOrderId'],
                'buy_price': resp['orderPrice'] + resp.get('freight', 0),
                'buy_from': u'武汉京东世纪贸易有限公司（慧采）'
            }
            info = {
                'status': ORDER_STATUS.WAIT_RECEIPT,
                'ship_status': SHIP_STATUS.SHIPPING_SUCCESS,
                'extend': json.dumps(extend, ensure_ascii=False)
            }
            update_order(order, info)
            return True
        else:
            extend['ship_msg'] = resp['msg']
            info = {
                'ship_status': SHIP_STATUS.SHIPPING_FAILED,
                'extend': json.dumps(extend, ensure_ascii=False)
            }
            update_order(order, info)
            if resp['code'] == '3008':  # 库存不足
                continue
            return False
    return False
