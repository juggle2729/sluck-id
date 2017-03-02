# -*- coding: utf-8 -*-
import json
import logging
from cStringIO import StringIO
from datetime import datetime

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_unicode
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import TemplateView

from luckyapi.logic.account import send_auth_code
from luckycommon.async.async_job import track_new_user, track_one
from luckycommon.account import handler as account_handler
from luckycommon.account import internal_handler as account_internal_handler
from luckycommon.account.db import account as account_db
from luckycommon.account.db.account import has_password, get_third_account_by_uid, create_third_account, get_third_account
from luckycommon.account.handler import check_auth_code
from luckycommon.account.model.account import ThirdAccountType
from luckycommon.cache import account as cache
from luckycommon.partner import handler as partner_handler
from luckycommon.push import handler as push_handler
from luckycommon.third import facebook_login
from luckycommon.third import google_login
from luckycommon.utils import exceptions as err
from luckycommon.utils.api import (token_required, get_client_ip, parse_p,
                                   get_city, check_params)
from luckycommon.utils.code import create_validate_code
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.respcode import StatusCode

_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


def _auto_nick_name(register_type, register_num):
    if 'email' == register_type:
        num = register_num
        pre, post = num.split('@')
        return pre[:-4] + '****' + '@' + post if len(pre) >= 4 else '*' * len(pre) + '@' + post
    else:
        num = register_num
        return num[2:5] + '****' + num[-4:]


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def strip_phone(phone_number):
    phone_number = str(phone_number)
    prefix_list = ['62', '0', '620', '062']
    for prefix in prefix_list:
        phone_number = remove_prefix(phone_number, prefix)
    return phone_number


@require_POST
@response_wrapper
def register(request):
    """
    注册用户
    1. 提交用户名/密码，系统发送验证码
    2. 重发验证码
    3. 创建账户
    """
    query_dct = json.loads(request.body)
    tracks = parse_p(request.GET.get('p'))
    check_params(query_dct, ('phone', 'password', 'auth_code'))
    register_type = 'phone'
    register_num = strip_phone(query_dct['phone'])
    exist_account = account_internal_handler.exists_account(register_type, register_num)
    if exist_account:
        raise err.DataError(status=StatusCode.DUPLICATE_ACCOUNT)

    auth_code_valid = check_auth_code(register_num, query_dct['auth_code'])
    if not auth_code_valid:
        raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)
    # 创建用户
    account_dct = {
        'password': query_dct['password']
    }
    if register_type == 'phone':
        account_dct.update({'phone': register_num})
    if register_type == 'email':
        account_dct.update({'email': register_num})
    nick_name = smart_unicode(query_dct.get('nick_name'))
    if not nick_name:
        nick_name = _auto_nick_name(register_type, register_num)
    # check nick name length
    nick_name = nick_name[:20]
    nick_name = nick_name.replace('%', '%25')
    account_dct.update({'nick_name': nick_name})
    account_dct.update({'country': tracks.get('code')})
    account = account_internal_handler.create_account(account_dct, channel=tracks.get('chn', 'none'), package=tracks.get('pkg', 'none'))
    try:
        account_handler.add_fresh_coupon(account.id)
        push_handler.push_fresh_award(account.id, is_coupon=True)
    except Exception as e:
        _LOGGER.error('add award error.(%s)' % e)
    inviter_id = query_dct.get('inviter_id')
    if inviter_id:
        try:
            partner_handler.bind_inviter(account.id, inviter_id)
        except err.ParamError:
            pass
    _TRACKER.info({"user_id": account.id, "type": "register",
                   "aid": tracks.get('aid', 'none'),
                   "chn": tracks.get('chn', 'none'),
                   "inviter_id": inviter_id or '',
                   "pkg": tracks.get('pkg'),
                   "code": tracks.get('code')})
    track_new_user.delay(account.id, {'is_virtual': False, 'channel': tracks.get('chn', None), 'register_at': datetime.now().isoformat()})
    track_one.delay('register', {'channel': tracks.get('chn', None), 'package': tracks.get('pkg', None)}, account.id)
    return {}


@require_POST
@response_wrapper
def login(request):
    try:
        query_dct = json.loads(request.body)
    except:
        raise err.ParamError('login invalid')
    check_params(query_dct, ['register_num', 'password'])
    login_type = 'phone'
    login_num = strip_phone(query_dct['register_num'])
    client_ip = get_client_ip(request)
    client_city = get_city(client_ip)
    extend = {
        'ip': client_ip,
        'addr': client_city
    }
    try:
        account, logon = account_internal_handler.login_account(login_type,
                                                                login_num,
                                                                query_dct['password'],
                                                                extend=extend)
        _TRACKER.info({"user_id": account.id, "type": "login", "logon": logon})
        return account_handler.get_user_info(account)
    except err.AuthenticateError as es:
        raise es


@require_POST
@response_wrapper
def third_login(request):
    query_dict = json.loads(request.body)
    third_account_type = query_dict.get('third_login_type')
    access_token = query_dict.get('access_token')
    inviter_id = query_dict.get('inviter_id')
    tracks = parse_p(request.GET.get('p'))
    _LOGGER.debug('register tracks: %s' % tracks)

    client_ip = get_client_ip(request)
    client_city = get_city(client_ip)
    extend = {
        'ip': client_ip,
        'addr': client_city
    }

    _LOGGER.debug('third_account_type: %s, ThirdAccountType.facebook.value: %s' % (third_account_type, ThirdAccountType.facebook.value))
    _LOGGER.debug(
        'third_account_type: %s, ThirdAccountType.facebook.value: %s' % (type(third_account_type), type(ThirdAccountType.facebook.value)))
    if third_account_type == ThirdAccountType.facebook.value:
        third_id, nickname, avatar_url = facebook_login.get_user_profile(access_token)
    else:
        raise err.ParamError('third_login_type not support')

    if not third_id:
        raise err.ThirdPartyError('get user third account profile failed')

    third_account = account_internal_handler.get_third_account(third_id, third_account_type)
    if not third_account:
        account_internal_handler.register_third_account(third_id, third_account_type, nickname, avatar_url,
                                                        tracks.get('chn', 'none'), tracks.get('pkg', 'none'))
        # auto login user, reduce one api call
        account, logon = account_internal_handler.login_third_account(third_id, third_account_type, extend)
        try:
            account_handler.add_fresh_coupon(account.id)
            push_handler.push_fresh_award(account.id, is_coupon=True)
        except Exception as e:
            _LOGGER.error('add award error.(%s)' % e)
        if inviter_id:
            try:
                partner_handler.bind_inviter(account.id, inviter_id)
            except err.ParamError:
                pass
        _TRACKER.info({"user_id": account.id,
                       "type": "register",
                       "aid": tracks.get('aid', 'none'),
                       "chn": tracks.get('chn', 'none'),
                       "inviter_id": inviter_id or '',
                       "pkg": tracks.get('pkg'),
                       "code": tracks.get('code'),
                       })
        _LOGGER.debug('id: %s, created_at: %s' % (account.id, account.created_at))
        return account_handler.get_user_info(account)
    else:
        account, logon = account_internal_handler.login_third_account(third_id, third_account_type, extend)
        _TRACKER.info({"user_id": account.id, "type": "login", "logon": logon})
        return account_handler.get_user_info(account)

@require_POST
@response_wrapper
@token_required
def third_bind(request):
    user_id = request.user_id
    query_dict = json.loads(request.body)
    phone = strip_phone(query_dict.get('phone'))
    auth_code = query_dict.get('auth_code')
    password = query_dict.get('password')
    third_account_type = query_dict.get('third_login_type')
    access_token = query_dict.get('access_token')
    # bind phone
    if phone and password and auth_code:
        if not check_auth_code(phone, auth_code):
            raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)
        account_dict = {
            'id': user_id,
            'phone': phone,
            'password': password
        }
        account_db.update_account(account_dict)
        return {}
    # bind third account
    if third_account_type and access_token:
        third_account = get_third_account_by_uid(user_id)
        if third_account:
            return {}

        if third_account_type == ThirdAccountType.facebook.value:
            third_id, nickname, avatar_url = facebook_login.get_user_profile(access_token)
        elif third_account_type == ThirdAccountType.google.value:
            third_id, nickname, avatar_url = google_login.get_user_profile(access_token)
        else:
            raise err.ParamError('third_login_type not support')

        if not third_id:
            raise err.ThirdPartyError('get user third account profile failed')

        third_account = get_third_account(third_id, third_account_type)
        if third_account:
            raise err.DataError(status=StatusCode.DUPLICATE_ACCOUNT)

        create_third_account(user_id, third_id, third_account_type)
        return {}

@require_GET
def create_image_code(req):
    phone = strip_phone(req.GET.get('phone'))
    if not phone:
        raise err.ParamError('invalid')
    image, code_str = create_validate_code()
    output = StringIO()
    image.save(output, 'PNG', quality=95)
    _LOGGER.info('create image code, phone:%s, code str:%s', phone, code_str)
    cache.set_image_code(phone, code_str)
    return HttpResponse(output.getvalue(), 'image/png')


@require_POST
@response_wrapper
def check_image_code(req):
    code = req.POST.get('code')
    phone = strip_phone(req.POST.get('phone'))
    if not code or not phone:
        raise err.ParamError('invalid')
    right_code = cache.get_image_code(phone)
    if not right_code or code.lower() != right_code.lower():
        # meanwhile, clear the code
        cache.clear_image_code(phone)
        raise err.ParamError('code invalid')
    # do send sms auth code
    ip = get_client_ip(req)
    send_auth_code(phone, ip=ip, need_check=False)
    return {}


class AuthCodeView(TemplateView):
    def get(self, req):
        """ send auth_code sms to client.
            required: phone num

            response: {}
        """
        query_dct = req.GET.dict()
        tracks = parse_p(req.GET.get('p'))
        check_params(query_dct, ('phone',), {'use': ''})
        phone = strip_phone(query_dct['phone'])
        exists = account_db.get_account_by_phone(phone)
        if query_dct['use'] == 'changepwd' and not exists:
            raise err.DataError(status=StatusCode.INVALID_USER)
        if query_dct['use'] == 'register' and exists and has_password(phone):   # in some case, user can register and not set password
            raise err.DataError(status=StatusCode.DUPLICATE_ACCOUNT)
        if query_dct['use'] == 'changephone' and exists:
            raise err.DataError(status=StatusCode.DUPLICATE_ACCOUNT)
        if query_dct['use'] == 'third_bind' and exists:
            raise err.DataError(status=StatusCode.DUPLICATE_ACCOUNT)
        ip = get_client_ip(req)
        return {} if send_auth_code(phone, ip=ip) else {'image': True}

    def post(self, req):
        """ check client input auth code
            required: phone, auth_code

            response: {} or error
        """
        query_dct = json.loads(req.body)
        check_params(query_dct, ('phone', 'auth_code'))
        phone_num = strip_phone(query_dct['phone'])
        is_right = check_auth_code(phone_num, query_dct['auth_code'])
        if is_right:
            return {}
        else:
            raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)

    @method_decorator(response_wrapper)
    def dispatch(self, *args, **kwargs):
        return super(AuthCodeView, self).dispatch(*args, **kwargs)


@require_POST
@response_wrapper
@token_required
def logout(request):
    """ user logout
        required: user login

        response:
            {}
    """
    account_internal_handler.logout_device(request.user_id, request.user.token)
    _TRACKER.info({"user_id": request.user_id, "type": "logout"})
    return {}


@require_POST
@response_wrapper
def forgot_password(request):
    """
    忘记密码
    """
    query_dct = request.GET
    check_params(query_dct, ['register_num'])
    register_type, register_num = account_handler.check_register_num(query_dct['register_num'])
    exist_account = account_internal_handler.exists_account(register_type, register_num)
    if not exist_account or not exist_account.email:
        raise err.DataError(status=StatusCode.INVALID_USER)
    account_handler.send_resetpwd_link(exist_account.email)
    return {}


@require_POST
@response_wrapper
def reset_password(request):
    query_dct = json.loads(request.body)
    check_params(query_dct, ['phone', 'auth_code', 'password'])
    phone_num = strip_phone(query_dct['phone'])
    if not check_auth_code(phone_num, query_dct['auth_code']):
        raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)
    else:
        account_handler.reset_password(phone_num, query_dct['password'])
        return {}
