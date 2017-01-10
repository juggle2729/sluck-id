# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.logic.show import (view_my_shows, view_show_detail,
                                 view_other_shows,
                                 view_shows_timeline, view_my_show_detail)

from luckycommon.model.show import AnnounceShow 
from luckycommon.db.show import get_show_by_template, update_show, verify_show

from luckycommon.campaign import fortune_wheel

from luckycommon.utils.api import token_required, filter_apples, filter_gp
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError, AuthenticateError

from future.utils import raise_with_traceback

from django.conf import settings
from django.utils.encoding import smart_unicode
from django.views.decorators.http import require_GET, require_POST


_LOGGER = logging.getLogger('lucky')
_DEFAULT_PAGE_SIZE = 20
DEBUG_USER = settings.DEBUG_USER


@require_GET
@response_wrapper
@token_required
def get_my_shows(request):
    """
    查看我的晒单记录
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    s_list = view_my_shows(request.user_id, page, size)
    data = {
        'list': s_list,
        'page': page if page > 0 else 1,
        'size': len(s_list)
    }
    return data


@require_GET
@response_wrapper
def get_other_shows(request, user_id):
    """
    查看他人的晒单记录
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    s_list = view_other_shows(user_id, page, size)
    s_list = filter_apples(request, s_list)
    s_list = filter_gp(request, s_list)
    data = {
        'list': s_list,
    }
    return data


@require_GET
@response_wrapper
@token_required
def get_my_show_detail(request):
    """
    获取晒单编号
    """
    try:
        gid = int(request.GET.get('gid'))
        term = int(request.GET.get('term'))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    show_detail = view_my_show_detail(request.user_id, gid, term)
    return show_detail


@require_GET
@response_wrapper
def get_timeline(request):
    """
    获取晒单分享
    """
    try:
        template_id = request.GET.get('gid')
        start_ts = int(request.GET.get('start_ts', 0))
        max_ts = int(request.GET.get('max_ts', -1))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    s_list = view_shows_timeline(start_ts, max_ts, template_id)
    s_list = filter_apples(request, s_list)
    s_list = filter_gp(request, s_list)
    data = {
        'list': s_list,
        'size': len(s_list)
    }
    return data 


@require_POST
@response_wrapper
@token_required
def edit(request, show_id):
    """
    编辑晒单
    """
    try:
        title = smart_unicode(request.POST.get('title', ''))
        content = smart_unicode(request.POST.get('content', ''))
        images = smart_unicode(request.POST.get('images', ''))
        if not content:
            raise ParamError('param invalid')
    except Exception as e:
        raise_with_traceback(ParamError(e))

    user_id = request.user_id

    update_show(user_id, show_id, title, content, images)
    fortune_wheel.callback_task(user_id, 6)
    return {}


@require_GET
@response_wrapper
def get_show_detail(request, show_id):
    """
    获取晒单详情 
    """
    show_detail = view_show_detail(request.user_id, show_id)
    return show_detail


@require_POST
@response_wrapper
@token_required
def verify(request, show_id):
    """
    审核晒单
    """
    if request.user_id != DEBUG_USER:
        raise AuthenticateError()
    try:
        is_verified = int(request.POST.get('ok', 0))
        tag = int(request.POST.get('tag', 0))
        verify_comment = request.POST.get('comment', '')
        verify_award = int(request.POST.get('verify_award', 100))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    verify_show(show_id, is_verified, verify_comment, verify_award, tag)
    return {}
