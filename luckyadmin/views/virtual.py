# -*- coding: utf-8 -*-

import json
import logging

from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_unicode
import xlrd

from luckycommon.db import virtual as db
from luckycommon.account.db.account import update_account
from luckycommon.cache.redis_cache import is_virtual_account
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.exceptions import PermissionError
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)


class AwaitVirtualView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = db.list_await_users(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            item.password = ""
            resp_items.append(item.as_dict())

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count,
                'unused_avatar_count': db.get_unused_count()}

    def post(self, req):
        if 'excel_data' in req.FILES:
            data = req.FILES['excel_data']
            imported_data = []
            book = xlrd.open_workbook(file_contents=data.read())
            sh = book.sheet_by_index(0)
            for x in range(sh.nrows):
                imported_data.append(sh.row_values(x))
            db.batch_insert_user(imported_data)
            return {}

        query_dct = json.loads(smart_unicode(req.body))
        user = db.upsert_await_user(query_dct)

        user.password = ""
        return user.as_dict()

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(AwaitVirtualView, self).dispatch(*args, **kwargs)


class SingleAwaitVirtualView(TemplateView):

    def get(self, req, user_id):
        user = db.get_await_user(int(user_id))
        user.password = ""
        user.updated_at = utc_to_local_str(user.updated_at)
        user.created_at = utc_to_local_str(user.created_at)
        return user.as_dict()

    def post(self, req, user_id):
        return self.put(req, user_id)

    def put(self, req, user_id):
        query_dct = json.loads(smart_unicode(req.body))
        query_dct['id'] = int(user_id)
        db.upsert_await_user(query_dct)

        return {}

    def delete(self, req, user_id):
        db.delete_user(int(user_id))
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleAwaitVirtualView, self).dispatch(*args, **kwargs)


@require_POST
@response_wrapper
@token_required
def upload_avatars(req):
    avatars = json.loads(req.body).get('avatars', [])
    db.add_avatars(avatars)

    return {}


@require_POST
@response_wrapper
@token_required
def update_virtual_account(req, user_id):
    if not is_virtual_account(long(user_id)):
        raise PermissionError("can't update real user avatar")
    data_dct = json.loads(req.body)
    update_account({
        'id': user_id,
        'avatar_id': data_dct.get('avatar_id')
    })
    return {}
