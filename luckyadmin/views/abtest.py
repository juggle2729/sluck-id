# -*- coding: utf-8 -*-

import json
import logging

from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator

from luckycommon.db import abtest as db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)


class ABTestView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = db.list_abtest(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            data = item.as_dict()
            data.update(json.loads(data['content'] or '{}'))
            data.pop('content', None)
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        query_dct = json.loads(smart_unicode(req.body))
        abtest = db.upsert_abtest(query_dct)
        _LOGGER.info('add abtest: %s, user: %s', abtest.as_dict(), req.user_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(ABTestView, self).dispatch(*args, **kwargs)


class SingleABTestView(TemplateView):

    def get(self, req, abtest_id):
        abtest = db.get_abtest(int(abtest_id))
        abtest.updated_at = utc_to_local_str(abtest.updated_at)
        abtest.created_at = utc_to_local_str(abtest.created_at)
        data = abtest.as_dict()
        data.update(json.loads(abtest.content or '{}'))
        data.pop('content', None)
        return data

    def put(self, req, abtest_id):
        query_dct = json.loads(smart_unicode(req.body))
        db.upsert_abtest(query_dct, int(abtest_id))
        _LOGGER.info(
            'update abtest info: %s, user: %s', query_dct, req.user_id)
        return {}

    def delete(self, req, abtest_id):
        db.delete_abtest(int(abtest_id))
        _LOGGER.info('delete abtest: %s, user: %s', abtest_id, req.user_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleABTestView, self).dispatch(*args, **kwargs)
