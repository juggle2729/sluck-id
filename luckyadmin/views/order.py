# -*- coding: utf-8 -*-

import json
import logging
import datetime

from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator
import xlrd

from luckycommon.order.handler import show_order

from luckycommon.push import handler as push_handler
from luckycommon.cache import redis_cache
from luckycommon.db.goods import get_goods
from luckycommon.db.activity import get_activity
from luckycommon.account.db.account import get_account
from luckycommon.order.model.order import ORDER_STATUS
from luckycommon.order.db import order as db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required, check_params
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.exceptions import SmsPlatformError, NotImplementedError
from luckycommon.utils.export import redirect_to_file, gen_filename

_LOGGER = logging.getLogger(__name__)


class OrderView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        export = query_dct.pop('$export', None)
        resp_items = []

        if export:
            filename = gen_filename('export_order')
            status = query_dct.get('status')
            data = None
            if status and int(status) == ORDER_STATUS.WAIT_SHIP:
                cn_header = [u'订单ID', u'用户ID', u'收货人', u'省', u'市', u'县',
                             u'街道', u'送货地址', u'收货人手机号', u'商品编号',
                             u'商品名称', u'备注']
                data = db.export_awarded_orders(query_dct)
            elif status and int(status) == ORDER_STATUS.AWARDED:
                cn_header = [u'订单ID', u'用户ID', u'收货人', u'省', u'市', u'县',
                             u'街道', u'送货地址', u'收货人手机号', u'商品编号',
                             u'商品名称', u'备注']
                data = db.export_awarded_orders(query_dct)
            elif status and int(status) == ORDER_STATUS.WAIT_RECEIPT:
                cn_header = [u'发货时间', u'订单ID', u'用户ID', u'活动名称',
                             u'快递名', u'快递单号', u'供货商', u'购买价格']
                data = db.export_sent_orders(query_dct)
            if data:
                return redirect_to_file(data, cn_header, filename)
            else:
                raise NotImplementedError('not support')

        # normal
        items, total_count, award_only = db.list_orders(query_dct, True)
        for item in items:
            order, is_virtual = item
            k = order.as_dict()
            if award_only:
                k['id'] = str(k.pop('order_id'))
                k['buyer'] = str(k.pop('user_id'))
            else:
                k['id'] = str(k['id'])
                k['buyer'] = str(k['buyer'])
            activity = get_activity(k['activity_id'])
            k['is_virtual'] = is_virtual
            k['activity_name'] = activity.name
            k['term_number'] = activity.term_number
            k['target_amount'] = activity.target_amount
            k['updated_at'] = utc_to_local_str(k['updated_at'])
            k['created_at'] = utc_to_local_str(k['created_at'])
            resp_items.append(k)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        # batch ship from excel
        if 'excel_data' in req.FILES:
            data = req.FILES['excel_data']
            imported_data = []
            book = xlrd.open_workbook(file_contents=data.read())
            sh = book.sheet_by_index(0)
            for x in range(sh.nrows):
                imported_data.append(sh.row_values(x))
            shipp_push = db.batch_ship_orders(imported_data, req.user_id)
            for order_id, shipping_info in shipp_push:
                try:
                    push_handler.push_shipping(order_id, shipping_info)
                except SmsPlatformError as e:
                    _LOGGER.error('FAIL to send notify', e)
                    continue
        else:
            # batch autoship jd
            params = json.loads(req.body)
            check_params(params, ['order_ids'])
            for order_id in params['order_ids']:
                db.send_order(order_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(OrderView, self).dispatch(*args, **kwargs)


class SingleOrderView(TemplateView):

    def get(self, req, order_id):
        item = db.get_awarded_order(long(order_id))
        if item:
            data = item.as_dict()
            data['id'] = str(data.pop('order_id'))
            data['buyer'] = str(data.pop('user_id'))
            data['advise_delivery_time'] = 'No Delay'
            if data['status'] in (5, 11):
                gp_flag = redis_cache.get_gp_delivery_timestamp(data['buyer'])
                extend = json.loads(data['extend'])
                if gp_flag:
                    award_time = extend.get('award_time')
                    advise_delivery_time = datetime.datetime.strptime(award_time, '%Y-%m-%d %H:%M:%S') \
                                           + datetime.timedelta(3)
                    data['advise_delivery_time'] = advise_delivery_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            item = db.get_order(long(order_id))
            data = item.as_dict()
            data['id'] = str(data['id'])
            data['buyer'] = str(data['buyer'])

        activity = get_activity(data['activity_id'])
        buyer = get_account(data['buyer'])
        data['buyer_phone'] = buyer.phone if buyer else ''
        data['target_amount'] = activity.target_amount
        goods = get_goods(activity.goods_id)
        data['is_virtual'] = redis_cache.is_virtual_account(data['buyer'])
        data['activity_name'] = activity.name
        data['term_number'] = activity.term_number
        data['source'] = goods.source if goods else 'unknown'
        data['goods_price'] = goods.price if goods else 'unknown'
        data['receipt_address'] = ''
        return data

    def post(self, req, order_id):
        return self.put(req, order_id)

    def put(self, req, order_id):
        query_dct = json.loads(smart_unicode(req.body))
        shipping_push, receipt_push = db.update_order_info(
            int(order_id), query_dct, req.user_id)
        extend = query_dct['extend']
        try:
            extend = json.loads(extend)
        except ValueError as e:
            _LOGGER.error('order extend invalid value, %s' % e)
        if shipping_push and isinstance(extend, dict):  # 确认发货
            shipping_info = {
                'express': extend.get('express'),
                'express_num': extend.get('express_num')
            }
            if not shipping_info['express']:
                shipping_info = {}
            push_handler.push_shipping(order_id, shipping_info)
        if shipping_push and not isinstance(extend, dict):  # 确认发货
            push_handler.push_shipping(order_id, {})
        if receipt_push:
            push_handler.push_receipt(order_id)
            # 创建晒单
            order = db.get_order(order_id)
            show_order(order)

        _LOGGER.info('update order %s info: %s, user: %s', order_id,
                     query_dct, req.user_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleOrderView, self).dispatch(*args, **kwargs)
