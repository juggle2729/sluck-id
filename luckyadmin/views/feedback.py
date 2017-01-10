# -*- coding: utf-8 -*-

import logging

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from luckycommon.feedback.db import feedback as db
from luckycommon.stats.device_track import (
    list_device_stats, calc_questionare_overview, calc_uninstall_overview)
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.export import redirect_to_file, gen_filename

_LOGGER = logging.getLogger(__name__)


class FeedbackView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        export = query_dct.pop('$export', None)
        resp_items = []
        if export:
            filename = gen_filename('feedback')
            header = ['user_id', 'qq', 'chn', 'cvc', 'created_at', 'content']
            cn_header = [u'用户ID', 'qq', u'渠道', u'版本号', u'创建时间', u'内容']

        items, total_count = db.list_feedback(query_dct)

        resp_items = []
        unique_items = set()
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            k = item.as_dict()
            if export:
                if not k.get('content'):
                    continue
                if k.get('user_id'):
                    if (k['user_id'], k['content']) in unique_items:
                        continue
                    else:
                        unique_items.add((k['user_id'], k['content']))
                resp_items.append([k.get(x, '-') for x in header])
            else:
                resp_items.append(k)

        if export:
            return redirect_to_file(resp_items, cn_header, filename)
        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(FeedbackView, self).dispatch(*args, **kwargs)


class UninstallView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        query_dct['remove_at'] = '$!null'
        items, total_count = list_device_stats(query_dct)
        resp_items = []
        for item in items:
            if 'created_at' in item:
                item['created_at'] = utc_to_local_str(item['created_at'])
            if 'remove_at' in item:
                item['remove_at'] = utc_to_local_str(item['remove_at'])
            resp_items.append(item)
        overview = {
            'questionare': calc_questionare_overview(),
            'uninstall': calc_uninstall_overview()
        }
        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count,
                'overview': overview}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(UninstallView, self).dispatch(*args, **kwargs)
