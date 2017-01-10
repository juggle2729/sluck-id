# -*- coding: utf-8 -*-

import json
import logging

from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator

from luckycommon.push import handler as push_handler
from luckycommon.cache.redis_cache import is_virtual_account
from luckycommon.db import show as db
from luckycommon.db.activity import get_template
from luckycommon.credit.db import credit as credit_db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required, check_params
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)

_SHOW_AWARD_TITLE = u'晒单奖励'


class ShowView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = db.list_shows(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            item_dct = item.as_dict()
            template = get_template(item.template_id)
            item_dct['template_name'] = template.name if template else ''
            item_dct['is_virtual'] = is_virtual_account(item.user_id)
            item_dct['order_id'] = str(item_dct['order_id'])
            resp_items.append(item_dct)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        data_dct = json.loads(smart_unicode(req.body))
        check_params(data_dct, ['activity_id', 'images', 'content'], {
            'title': ''})
        return db.create_virtual_show(data_dct)

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(ShowView, self).dispatch(*args, **kwargs)


class SingleShowView(TemplateView):

    def get(self, req, show_id):
        show = db.get_show_by_id(int(show_id))
        show.updated_at = utc_to_local_str(show.updated_at)
        show.created_at = utc_to_local_str(show.created_at)
        result = show.as_dict()
        template = get_template(show.template_id)
        result['template_name'] = template.name if template else ''
        result['is_virtual'] = is_virtual_account(show.user_id)
        result['order_id'] = str(result['order_id'])

        return result

    def post(self, req, show_id):
        return self.put(req, show_id)

    def put(self, req, show_id):
        show_id = int(show_id)
        query_dct = json.loads(smart_unicode(req.body))
        status = int(query_dct.get('status', 0))
        mutable_dct = {}
        for k in 'content', 'highlight', 'title', 'images':
            if k in query_dct:
                mutable_dct[k] = query_dct[k]
        if mutable_dct:
            db.update_mutable(show_id, mutable_dct)
        show, need_award, need_push_fail = db.verify_show(
            show_id, status, query_dct.get('verify_comment', ''),
            int(query_dct.get('verify_award', 0)),
            int(query_dct.get('highlight', 0)))
        if need_award:
            # add credit award by verify award
            award_credit = show.verify_award
            credit_db.add_credit(show.user_id, award_credit, _SHOW_AWARD_TITLE)
            push_handler.push_show_award(show)
        if need_push_fail:
            push_handler.push_verify_fail(show)
        _LOGGER.info('update show info: %s, user: %s', query_dct, req.user_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleShowView, self).dispatch(*args, **kwargs)
