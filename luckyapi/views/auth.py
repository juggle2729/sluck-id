# -*- coding: utf-8 -*-
import json
import logging
import hashlib
from cStringIO import StringIO
from datetime import datetime, timedelta

from django.views.decorators.http import require_POST, require_GET
from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator
from django.http import HttpResponse

from luckyapi.logic.account import (COUNTRY_CODE_DCT, send_auth_code, check_auth_code,
                                    add_fresh_coupon, upload_avatar, get_fixed_num)
from luckycommon.mission import fresh_mission
from luckycommon.level.handler import get_level_dict
from luckycommon.push import handler as push_handler
from luckycommon.partner import handler as partner_handler
from luckycommon.cache import account as cache
from luckycommon.db import account as db
from luckycommon.db.transaction import add_system_award_transaction
from luckycommon.db.account import need_set_password, reset_passwd, get_account
from luckycommon.db.coupon import check_awaiting_coupon
from luckycommon.db.partner import get_user_inviter
from luckycommon.utils.exceptions import ParamError
from luckycommon.utils.template import generate_from_template
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils import exceptions as err
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils import tz
from luckycommon.utils.qr import make_qr
from luckycommon.utils.code import create_validate_code
from luckycommon.utils.api import (token_required, get_client_ip,
                                   get_client_ua, get_city, check_params, parse_p)

from django.conf import settings

_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


def get_user_type(account):
    registered_at = account.created_at.date()
    now_dt = datetime.utcnow().date()
    if now_dt == registered_at:
        # 新用户
        return 1
    elif now_dt - registered_at == timedelta(days=1):
        # 次日用户
        return 2
    elif now_dt - registered_at <= timedelta(days=6):
        # 周用户
        return 3
    else:
        # 老用户
        return 4


def _get_user_info(user):
    phone_num = user.phone[2:]
    inviter_item = get_user_inviter(user.id)
    level_dict = get_level_dict(user.id)
    data = {
        'id': str(user.id),
        'type': get_user_type(user),
        'register_ts': tz.to_ts(user.created_at),
        'phone': phone_num,
        'avatar_id': user.avatar_id,
        'nick_name': user.nick_name,
        'email': user.email,
        'balance': user.balance,
        'credit': user.credit,
        'country': user.country,
        'token': user.token,
        'level': level_dict['current_level'],
        'level_icon': level_dict['level_icon'],
        'level_name': level_dict['level_name']
    }
    if inviter_item:
        inviter_id = inviter_item.inviter_id
        inviter_account = get_account(inviter_id)
        data.update({
            'inviter_id': inviter_id,
            'inviter_name': inviter_account.nick_name
        })
    return data


@require_GET
@response_wrapper
def get_public_profile(req):
    try:
        user_id = int(req.GET.get('user_id'))
    except:
        raise ParamError('parameter `user_id` invalid')
    level_dict = get_level_dict(user_id)
    data = {
        'level': level_dict['current_level'],
        'level_icon': level_dict['level_icon'],
        'level_name': level_dict['level_name'],
        'level_icon_big': level_dict['level_icon_big']
    }
    return data


@require_POST
@response_wrapper
def login(req):
    """ user login
        required: phone, password
        optional: device_type, os_version

        response:
            {
                'user_id': 'xxxx',
                'token': 'xxxx'
            }
    """
    query_dct = json.loads(req.body)
    check_params(query_dct, ['phone', 'password'], {
        'device_type': '', 'os_version': ''})
    client_ip = get_client_ip(req)
    client_city = get_city(client_ip)
    extend = {
        'ip': client_ip,
        'addr': client_city
    }
    query_dct['phone'] = get_fixed_num(query_dct['phone'])
    try:
        user, logon = db.login_account(query_dct['phone'],
                                       query_dct['password'],
                                       query_dct['device_type'],
                                       query_dct['os_version'],
                                       extend=extend)
        _TRACKER.info({"user_id": user.id, "type": "login", "logon": logon})
        return _get_user_info(user)
    except err.AuthenticateError as es:
        # check third account
        if need_set_password(query_dct['phone']):
            raise err.DataError(status=StatusCode.UXIN_ACCOUNT)
        raise es


@require_POST
@response_wrapper
@token_required
def logout(req):
    """ user logout
        required: user login

        response:
            {}
    """
    db.logout_device(req.user_id, req.user.token)
    return {}


@require_GET
def get_qr_code(req):
    user_id = req.user_id or req.GET.get('uid')
    source = req.GET.get('source') or 'qr'
    if user_id:
        url_text = '%s?uid=%s&source=%s' % (settings.INVITER_SHARE_LINK, user_id, source)
    else:
        url_text = settings.INVITER_SHARE_LINK
    image = make_qr(url_text)
    output = StringIO()
    image.save(output, 'PNG', quality=95)
    _LOGGER.info('create qr code, uid:%s', user_id)
    return HttpResponse(output.getvalue(), 'image/png')


@require_GET
def create_image_code(req):
    phone = req.GET.get('phone')
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
    phone = req.POST.get('phone')
    if not code or not phone:
        raise err.ParamError('invalid')
    right_code = cache.get_image_code(phone)
    if not right_code or code.lower() != right_code.lower():
        # meanwhile, clear the code
        cache.clear_image_code(phone)
        raise err.ParamError('code invalid')
    # do send sms auth code
    phone = get_fixed_num(phone)
    ip = get_client_ip(req)
    code = send_auth_code(phone, ip=ip, need_check=False)
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
        phone = get_fixed_num(query_dct['phone'])
        exists = db.exists_phone(phone)
        if query_dct['use'] == 'changepwd' and not exists:
            raise err.DataError(status=StatusCode.INVALID_USER)
        if query_dct['use'] == 'register' and exists and not need_set_password(phone):
            raise err.DataError(status=StatusCode.DUPLICATE_ACCOUNT)
        ip = get_client_ip(req)
        if query_dct['use'] == 'changepwd' or tracks:
            return {} if send_auth_code(phone, ip=ip) else {'image': True}
        else:
            return {'image': True}

    def post(self, req):
        """ check client input auth code
            required: phone, auth_code

            response: {} or error
        """
        query_dct = json.loads(req.body)
        check_params(query_dct, ('phone', 'auth_code'))
        query_dct['phone'] = get_fixed_num(query_dct['phone'])
        is_right = check_auth_code(query_dct['phone'], query_dct['auth_code'])
        if is_right:
            return {}
        else:
            raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)

    @method_decorator(response_wrapper)
    def dispatch(self, *args, **kwargs):
        return super(AuthCodeView, self).dispatch(*args, **kwargs)


class UserView(TemplateView):
    """register(post), list(get), and update(put) user info"""

    @method_decorator(token_required)
    def get(self, req, *args, **kwargs):
        """get user info.
        """
        return _get_user_info(req.user)

    def _auto_nick_name(self, phone):
        if not phone:
            return ''
        phone = phone[2:]
        return '%s****%s' % (phone[:3], phone[-4:])

    def post(self, req):
        """ register new user.
        """
        query_dct = json.loads(req.body)
        tracks = parse_p(req.GET.get('p'))
        check_params(query_dct, ('phone', 'password', 'auth_code'), {
            'email': '', 'country': settings.COUNTRY, 'nick_name': '',
            'avatar': '', 'avatar_id': ''})
        query_dct['phone'] = get_fixed_num(query_dct['phone'])
        if not check_auth_code(query_dct['phone'], query_dct['auth_code']):
            raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)
        if need_set_password(query_dct['phone']):
            reset_passwd(query_dct['phone'], query_dct['password'])
            return {'bind': 'uxin'}
        query_dct['nick_name'] = smart_unicode(query_dct['nick_name'])
        if not query_dct['nick_name']:
            query_dct['nick_name'] = self._auto_nick_name(query_dct['phone'])
        # check nick name length
        query_dct['nick_name'] = query_dct['nick_name'][:20]
        query_dct['nick_name'] = query_dct['nick_name'].replace('%', '%25')
        query_dct['avatar_id'] = smart_unicode(query_dct['avatar_id'])
        avatar_data = query_dct.pop('avatar')

        ip = get_client_ip(req)
        ip_checked = cache.check_ip_register_count(ip)
        if not ip_checked:
            _LOGGER.warn('check register ip fail, ip:%s', ip)
            return {}

        device_id = tracks.get('aid', 'none')
        device_checked = cache.check_device_register_count(device_id)
        if not device_checked:
            _LOGGER.warn('check register device fail, device:%s', device_id)
            return {}

        account = db.create_account(query_dct, chn=tracks.get('chn', 'none'))
        # add system award
        try:
            #chn = tracks.get('chn')
            #if not device_id or not chn or chn in settings.FRESH_COUPON_CHN_LIST:
            #    add_fresh_coupon(account.id)
            #    push_handler.push_fresh_award(account.id, is_coupon=True)
            #else:
            #    add_system_award_transaction(account.id)
            #    push_handler.push_fresh_award(account.id)
            add_fresh_coupon(account.id)
            push_handler.push_fresh_award(account.id, is_coupon=True)

            if avatar_data:
                url = upload_avatar(avatar_data)
                db.update_account({'id': account.id, 'avatar_id': url})
        except Exception as e:
            _LOGGER.error('add award error.(%s)' % e)
        # check awaiting coupon
        try:
            check_awaiting_coupon(account.id, account.phone)
        except Exception as e:
            _LOGGER.error('check coupon error.(%s)' % e)
        # check inviter
        inviter_id = None
        if query_dct.get('inviter_id'):
            inviter_id = query_dct.get('inviter_id')
            try:
                partner_handler.bind_inviter(account.id, inviter_id)
            except:
                inviter_id = None
        else:
            client_ip = get_client_ip(req)
            ua = get_client_ua(req)
            track_str = '%s' % (client_ip)
            # track_key = hashlib.md5(track_str).hexdigest()
            inviter_id = partner_handler.bind_inviter_by_track(account.id, track_str)
        _TRACKER.info({"user_id": account.id, "type": "register",
                       "aid": tracks.get('aid', 'none'),
                       "chn": tracks.get('chn', 'none'),
                       "inviter_id": inviter_id or ''})
        return {}

    def reset_passwd(self, query_dct):
        check_params(query_dct, ('phone', 'auth_code', 'password'))
        query_dct['phone'] = get_fixed_num(query_dct['phone'])
        if not check_auth_code(query_dct['phone'], query_dct['auth_code']):
            raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)
        else:
            user_id = db.reset_passwd(
                query_dct['phone'], query_dct['password'])
            db.logout_user(user_id)
        return {}

    def put(self, req):
        query_dct = json.loads(req.body)
        valid_params = {}
        if not req.user_id:
            return self.reset_passwd(query_dct)

        valid_params['id'] = req.user_id
        for k in ('phone', 'password', 'nick_name', 'email', 'country',
                  'avatar', 'avatar_id'):
            if k in query_dct:
                valid_params[k] = query_dct[k]
        if 'password' in valid_params:
            check_params(query_dct, ('old_password',))
            user = req.user
            if db.encode_password(query_dct['old_password']) != user.password:
                raise err.AuthenticateError(status=StatusCode.WRONG_PASSWORD)

        if 'phone' in valid_params:
            check_params(query_dct, ('auth_code',))
            auth_code = query_dct['auth_code']
            valid_params['phone'] = get_fixed_num(valid_params['phone'])
            if not check_auth_code(valid_params['phone'], auth_code):
                raise err.AuthenticateError(status=StatusCode.WRONG_AUTH_CODE)

        if 'avatar' in valid_params:
            url = upload_avatar(valid_params.pop('avatar'), req.user.avatar_id)
            valid_params['avatar_id'] = url

        if 'nick_name' in valid_params:
            valid_params['nick_name'] = smart_unicode(
                valid_params['nick_name'])
            valid_params['nick_name'] = valid_params['nick_name'][:20]
            valid_params['nick_name'] = valid_params['nick_name'].replace('%', '%25')
        account = db.update_account(valid_params)
        if account.nick_name and account.avatar_id:
            fresh_mission.check_step_b(req.user_id)

        for k in 'phone', 'password':
            if k in valid_params:
                db.logout_user(req.user_id)

        return {'avatar_id': valid_params['avatar_id']} if 'avatar_id' in valid_params else {}

    @method_decorator(token_required)
    def delete(self, req, *args, **kwargs):
        raise NotImplementedError()

    @method_decorator(response_wrapper)
    def dispatch(self, *args, **kwargs):
        return super(UserView, self).dispatch(*args, **kwargs)
