# -*- coding: utf-8 -*-

import logging

from luckycommon.account.model.account import AccountStatus
from luckycommon.account.db import account as api_user
from luckycommon.db import admin as admin_user
from luckycommon.utils.decorator import JsonResponse
from luckycommon.utils.exceptions import PermissionError

_LOGGER = logging.getLogger(__name__)


def check_perm(url_array, perm, role):
    l = len(url_array)
    while l >= 1:
        url = '/'.join(url_array[0:l])
        if not url.endswith('/'):
            url += '/'
        k = admin_user.get_perm(url, perm)
        if k and k.min_role <= role:
            return True
        l -= 1
    return False


class UserMiddleware(object):

    """get user_id and token from header"""

    def process_request(self, req):
        user_id, token = req.META.get(
            'HTTP_X_AUTH_USER'), req.META.get('HTTP_X_AUTH_TOKEN')
        if not user_id:
            user_id, token = req.COOKIES.get('lucky_user_id'), req.COOKIES.get(
                'lucky_user_token')
        if user_id and token:
            try:
                user_id = long(user_id)
            except ValueError:
                _LOGGER.error('user id format wrong!')
                req.user_id = None
                return
            if req.path.startswith('/api'):
                user = api_user.get_account(user_id)
                # check banned
                if not user or user.status == AccountStatus.BANNED.value:
                    # raise PermissionError('forbidden')
                    req.user_id = req.user = None
                    return
                info = api_user.get_online_info(user_id, token)
                if info and info.deleted == 0:
                    req.user_id = user_id
                    for k in 'token', 'device_type', 'os_version', 'extend':
                        v = getattr(info, k)
                        setattr(user, k, v)
                    req.user = user
                    return
                else:
                    _LOGGER.error(
                        "can't find user_id:%s, token:%s", user_id, token)
            else:
                info = admin_user.get_online_info(user_id, token)
                if info and info.deleted == 0:
                    req.user_id = user_id
                    user = admin_user.get_user(user_id)
                    if user.role > 0:
                        url_array = req.path.split('/')
                        if req.method == 'GET':
                            need_perm = 1
                        else:
                            need_perm = 2
                        if not check_perm(url_array, need_perm, user.role):
                            return JsonResponse(dict(
                                status=PermissionError.STATUS,
                                msg=str('permission not enough')),
                                status=PermissionError.HTTPCODE)
                        else:
                            req.user = user
                            return
                    else:
                        return JsonResponse(dict(
                            status=PermissionError.STATUS,
                            msg=str("user is forbidden or not activited")),
                            status=PermissionError.HTTPCODE)

        req.user_id = req.user = None
