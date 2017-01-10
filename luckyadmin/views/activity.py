# -*- coding: utf-8 -*-

import json
import logging

from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator

from luckycommon.db import activity as db
from luckycommon.db.show import count_show_by_template, get_show_by_template
from luckycommon.db.category import get_related_category, set_category
from luckycommon.model.activity import TEMPLATE_STATUS
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils import exceptions as err
from luckycommon.utils.api import token_required, dict2obj
from luckycommon.utils.tz import utc_to_local_str
from luckyapi.logic.crowdfunding import start_next_activity

_LOGGER = logging.getLogger(__name__)


class ActivityTemplateView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        calc_show = query_dct.pop('calc_show', None)
        items, total_count = db.list_templates(query_dct)
        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            data = item.as_dict()
            if data['status'] != 0:
                if data['added_at'] is None:
                    data['start_at'] = utc_to_local_str(
                        db.get_start_time(item.id))
                else:
                    data['start_at'] = utc_to_local_str(
                        data['added_at'])
            data['category_ids'] = []
            categorys = get_related_category(data['id'])
            for category in categorys:
                data['category_ids'].append(category.category_id)
            # for expensive show list...
            if calc_show is not None:
                data['show_count'] = count_show_by_template(item.id)
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        query_dct = json.loads(smart_unicode(req.body))
        category_ids = query_dct.pop('category_ids', [])
        new_template = db.create_template(dict2obj(query_dct))
        set_category(new_template.id, category_ids)
        _LOGGER.info('create template: %s, user: %s', new_template.as_dict(),
                     req.user_id)
        return {'id': new_template.id}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(ActivityTemplateView, self).dispatch(*args, **kwargs)


class SingleActivityTemplateView(TemplateView):

    def get(self, req, template_id):
        d = db.get_template(int(template_id))
        d.updated_at = utc_to_local_str(d.updated_at)
        d.created_at = utc_to_local_str(d.created_at)
        data = d.as_dict()
        if data['status'] != 0:
            if data['added_at'] is None:
                data['start_at'] = utc_to_local_str(
                    db.get_start_time(d.id))
            else:
                data['start_at'] = utc_to_local_str(
                    data['added_at'])
        categorys = get_related_category(int(template_id))
        data['category_ids'] = []
        for category in categorys:
            data['category_ids'].append(category.category_id)
        return data

    def post(self, req, template_id):
        return self.put(req, template_id)

    def put(self, req, template_id):
        template_id = int(template_id)
        query_dct = json.loads(smart_unicode(req.body))
        # delete some read-only key
        query_dct.pop('current_term', None)
        category_ids = query_dct.pop('category_ids', None) or []
        set_category(template_id, category_ids)
        need_start = db.update_template(template_id, query_dct)
        _LOGGER.info('update template %s, %s, user: %s', template_id, query_dct, req.user_id)
        if need_start:
            try:
                start_next_activity(0, template_id)
                _LOGGER.info(
                    'start template %s, user:%s', template_id, req.user_id)
            except Exception as e:
                db.update_template(
                    template_id, {'status': TEMPLATE_STATUS.PAUSED})
                _LOGGER.exception(
                    'start template %s error.(%e)', template_id, e)
                raise err.ResourceInsufficient('stock insufficient.(%s)' % e)

        return {}

    def delete(self, req, template_id):
        db.delete_template(int(template_id))
        _LOGGER.info('delete template: %s, user: %s', template_id, req.user_id)

        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(
            SingleActivityTemplateView, self).dispatch(*args, **kwargs)


class ActivityListView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        query_dct.pop('calc_show', None)
        items, total_count = db.list_activities(query_dct)
        resp_items = []
        for item in items:
            activity, winner, is_virtual = item
            data = activity.as_dict()
            data['updated_at'] = utc_to_local_str(data['updated_at'])
            data['created_at'] = utc_to_local_str(data['created_at'])
            data['announced_at'] = utc_to_local_str(data['announced_at'])
            data['winner'] = winner
            data['is_virtual'] = is_virtual
            data['show'] = get_show_by_template(
                activity.template_id, activity.term_number)
            if data['show']:
                data['show'] = data['show'].as_dict()
            else:
                data.pop('show')

            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(ActivityListView, self).dispatch(*args, **kwargs)
