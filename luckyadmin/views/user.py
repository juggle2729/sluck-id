# -*- coding: utf-8 -*-

import json
import logging

from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator

from luckycommon.db import admin as db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils import exceptions as err
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils.api import check_params, token_required
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.order.db.order import get_awardorder_info 
from luckycommon.db.transaction import get_transaction_info
from luckycommon.account.db.account import get_account_status

_LOGGER = logging.getLogger(__name__)


@require_POST
@response_wrapper
def login(req):
    query_dct = json.loads(req.body)
    check_params(query_dct, ('email', 'password'))

    user = db.login_user(query_dct['email'],
                         query_dct['password'])

    return user


@require_POST
@response_wrapper
@token_required
def logout(req):
    db.logout_device(req.user_id, req.user.token)
    return {}


class UserView(TemplateView):

    @method_decorator(token_required)
    def get(self, req, *args, **kwargs):
        query_dct = req.GET.dict()
        items, total_count = db.list_users(query_dct, req.user.role)
        resp_items = []
        for item in items:
            data = item.as_dict()
            data.pop('password', None)
            data['updated_at'] = utc_to_local_str(data['updated_at'])
            data['created_at'] = utc_to_local_str(data['created_at'])
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        query_dct = json.loads(req.body)
        check_params(query_dct, ('email', 'password'), {
            'nickname': ''
        })
        query_dct['nickname'] = smart_unicode(query_dct['nickname'])
        if 'adsquare-tech' not in query_dct['email']:
            raise err.AuthenticateError('please use adsquare-tech email')
        db.create_user(query_dct['email'], query_dct['password'],
                       query_dct['nickname'])

        _LOGGER.info('register user: %s', query_dct)
        return {}

    @method_decorator(response_wrapper)
    def dispatch(self, *args, **kwargs):
        return super(UserView, self).dispatch(*args, **kwargs)


class SingleUserView(TemplateView):

    def get(self, req, user_id):
        user_id = long(user_id)

        info = db.get_user(user_id).as_dict()
        if req.user.id != user_id and req.user.role < info['role']:
            raise err.PermissionError()
        else:
            info['created_at'] = utc_to_local_str(info['created_at'])
            info['updated_at'] = utc_to_local_str(info['updated_at'])
            info.pop('password', None)
            return info

    def put(self, req, user_id):
        query_dct = json.loads(req.body)
        valid_params = {}
        valid_params['id'] = int(user_id)
        for k in ('nickname', 'password', 'role'):
            if k in query_dct:
                valid_params[k] = query_dct[k]

        # if 'password' in valid_params:
        #     check_params(query_dct, ('old_password', ))
        #     user = req.user
        #     if db.encode_password(query_dct['old_password']) != user.password:
        #         raise err.AuthenticateError(status=StatusCode.WRONG_PASSWORD)
        if 'nickname' in valid_params:
            valid_params['nickname'] = smart_unicode(
                valid_params['nickname'])

        db.update_user(valid_params, req.user)

        if 'password' in valid_params:
            db.logout_user(req.user_id)

        _LOGGER.info('update user: %s, by %s', query_dct, req.user.id)
        return {}

    def delete(self, req, user_id):
        user = db.get_user(int(user_id))
        if user:
            if user.role >= req.user.role:
                raise err.PermissionError()
            else:
                user.delete()
        _LOGGER.info('delete user %s, by %s', user_id, req.user.id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleUserView, self).dispatch(*args, **kwargs)


class PermissionView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = db.list_perm(query_dct)
        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            data = item.as_dict()
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(PermissionView, self).dispatch(*args, **kwargs)


class SinglePermissionView(TemplateView):

    def get(self, req, perm_id):
        perm_id = int(perm_id)
        return db.get_perm(id=perm_id).as_dict()

    def post(self, req, perm_id):
        return self.put(req, perm_id)

    def put(self, req, perm_id):
        perm_id = int(perm_id)
        query_dct = json.loads(req.body)
        if 'min_role' in query_dct:
            min_role = int(query_dct['min_role'])
            db.update_perm(perm_id, min_role)

        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SinglePermissionView, self).dispatch(*args, **kwargs)


class WinnerUserView(TemplateView):

    _allow_admin_list=[17, 0, 0, 0]

    #@method_decorator(token_required)
    def get(self, req, user_id):
        user_id = long(user_id)
	info = db.get_user(user_id)
        if req.user.id not in self._allow_admin_list:
            return {"result_info": "not allow access!"}
        account_info = True if get_account_status(user_id) else False
        transaction_info = get_transaction_info(user_id)
        wining_info = get_transaction_info(user_id)
        result = {"user_id": user_id, \
		  "account_info": account_info, \
		  "transaction_info": transaction_info, \
		  "wining_info": wining_info}
	return result

    @method_decorator(response_wrapper)
    #@method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(WinnerUserView, self).dispatch(*args, **kwargs)

