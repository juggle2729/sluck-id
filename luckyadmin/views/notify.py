# -*- coding: utf-8 -*-
import json
import logging

from django.utils.encoding import smart_unicode
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from luckycommon.notification.db import notification as db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required, check_params
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)


class NotificationView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = db.list_sys_notification(query_dct)
        resp_items = []
        for item in items:
            data = item.as_dict()
            for k in 'content', 'extend':
                data[k] = json.loads(data[k] or '{}')
            for k in 'updated_at', 'created_at':
                data[k] = utc_to_local_str(data[k])
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'total_count': total_count, 'size': len(resp_items)}

    def post(self, req):
        param_dct = json.loads(smart_unicode(req.body))
        check_params(param_dct, ['content'], {'extend': ''})

        db.generate_sys_notification(
            param_dct['content'], extend=param_dct['extend'])
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(NotificationView, self).dispatch(*args, **kwargs)


class SingleNotificationView(TemplateView):

    def get(self, req, notify_id):
        notify_id = long(notify_id)
        item = db.get_sys_notification(notify_id)
        data = item.as_dict()
        for k in 'content', 'extend':
            data[k] = json.loads(data[k] or '{}')
        for k in 'updated_at', 'created_at':
            data[k] = utc_to_local_str(data[k])
        return data

    def put(self, req, notify_id):
        notify_id = long(notify_id)
        param_dct = json.loads(smart_unicode(req.body))

        db.update_sys_notification(param_dct, notify_id)
        return {}

    def delete(self, req, notify_id):
        notify_id = long(notify_id)
        db.delete_sys_notification(notify_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleNotificationView, self).dispatch(*args, **kwargs)
