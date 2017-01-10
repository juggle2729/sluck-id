# -*- coding: utf-8 -*-

import json
import logging

from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator

from luckycommon.db import category as db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)


class CategoryView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items = db.get_all_categorys()
        total_count = len(items)
        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            resp_items.append(item.as_dict())

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        # here is batch post
        query_list = json.loads(smart_unicode(req.body))
        db.batch_upsert(query_list)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(CategoryView, self).dispatch(*args, **kwargs)


class SingleCategoryView(TemplateView):
    def get(self, req, category_id):
        category = db.get_category(category_id)
        return category.as_dict()

    def delete(self, req, category_id):
        category_id = int(category_id)
        db.delete_category(category_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleCategoryView, self).dispatch(*args, **kwargs)
