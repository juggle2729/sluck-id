# -*- coding: utf-8 -*-
import json
import logging
from cStringIO import StringIO

from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import smart_unicode
from django.views.decorators.http import require_GET, require_POST

from luckyapi.account.auth import strip_phone
from luckycommon.account import handler as account_handler
from luckycommon.account.db import account as account_db
from luckycommon.account.handler import check_auth_code
from luckycommon.level.handler import get_level_dict
from luckycommon.mission import fresh_mission
from luckycommon.utils import exceptions as err
from luckycommon.utils.api import token_required, check_params
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.qr import make_qr
from luckycommon.utils.respcode import StatusCode

_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@require_GET
@response_wrapper
@token_required
def get_user(request):
    return account_handler.get_user_info(request.user)


@require_POST
@response_wrapper
@token_required
def modify_user(request):
    query_dct = json.loads(request.body)
    valid_params = {}
    valid_params['id'] = request.user_id
    for k in ('phone', 'password', 'nick_name', 'desc', 'country', 'avatar_id'):
        if k in query_dct:
            valid_params[k] = query_dct[k]
    if 'password' in valid_params:
        check_params(query_dct, ('old_password',))
        user = request.user
        if account_db.encode_password(query_dct['old_password']) != user.password:
            raise err.AuthenticateError(status=StatusCode.WRONG_PASSWORD)

    if 'phone' in valid_params:
        check_params(query_dct, ('auth_code',))
        auth_code = query_dct['auth_code']
        valid_params['phone'] = strip_phone(valid_params['phone'])
        phone = valid_params['phone']
        if not check_auth_code(phone, auth_code):
            raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)

    if 'nick_name' in valid_params:
        valid_params['nick_name'] = smart_unicode(
            valid_params['nick_name'])
        valid_params['nick_name'] = valid_params['nick_name'][:20]
        valid_params['nick_name'] = valid_params['nick_name'].replace('%', '%25')

    if 'desc' in valid_params:
        valid_params['desc'] = smart_unicode(valid_params['desc'])
        valid_params['desc'] = valid_params['desc'][:100]
        valid_params['desc'] = valid_params['desc'].replace('%', '%25')
    account = account_db.update_account(valid_params)
    if account.nick_name and account.avatar_id:
        fresh_mission.check_step_b(request.user_id)

    for k in 'phone', 'password':
        if k in valid_params:
            account_db.logout_user(request.user_id)
    return {}


@require_GET
@response_wrapper
def get_public_profile(request):
    try:
        user_id = int(request.GET.get('user_id'))
    except:
        raise err.ParamError('parameter `user_id` invalid')
    account = account_db.get_account(user_id)
    level_dict = get_level_dict(user_id)
    data = {
        'desc': account.desc,
        'level': level_dict['current_level'],
        'level_icon': level_dict['level_icon'],
        'level_name': level_dict['level_name'],
        'level_icon_big': level_dict['level_icon_big']
    }
    return data


@require_GET
def get_qr_code(request):
    user_id = request.user_id or request.GET.get('uid')
    source = request.GET.get('source') or 'qr'
    if user_id:
        url_text = '%s?uid=%s&source=%s' % (settings.INVITER_SHARE_LINK, user_id, source)
    else:
        url_text = settings.INVITER_SHARE_LINK
    image = make_qr(url_text)
    output = StringIO()
    image.save(output, 'PNG', quality=95)
    _LOGGER.info('create qr code, uid:%s', user_id)
    return HttpResponse(output.getvalue(), 'image/png')
