# -*- coding: utf-8 -*-

import json
import logging

from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator

from luckycommon.db import goods as db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)


class GoodsView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = db.list_goods(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            resp_items.append(item.as_dict())

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        query_dct = json.loads(smart_unicode(req.body))
        goods = db.create_goods(query_dct)
        _LOGGER.info('add goods: %s, user: %s', goods.as_dict(), req.user_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(GoodsView, self).dispatch(*args, **kwargs)


class SingleGoodsView(TemplateView):

    def get(self, req, goods_id):
        goods = db.get_goods(int(goods_id))
        goods.updated_at = utc_to_local_str(goods.updated_at)
        goods.created_at = utc_to_local_str(goods.created_at)
        return goods.as_dict()

    def post(self, req, goods_id):
        return self.put(req, goods_id)

    def put(self, req, goods_id):
        query_dct = json.loads(smart_unicode(req.body))
        db.modify_good_info(int(goods_id), query_dct)
        _LOGGER.info('update goods info: %s, user: %s', query_dct, req.user_id)
        return {}

    def delete(self, req, goods_id):
        db.delete_goods(int(goods_id))
        _LOGGER.info('delete goods: %s, user: %s', goods_id, req.user_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleGoodsView, self).dispatch(*args, **kwargs)
