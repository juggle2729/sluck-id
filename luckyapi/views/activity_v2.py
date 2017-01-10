# -*- coding: utf-8 -*-
import logging

from luckyapi.logic.crowdfunding import (create_activity_template,
                                         start_next_activity,
                                         view_my_activitys_v2,
                                         view_other_activitys,
                                         view_activity_detail,
                                         view_activity_revealed,
                                         view_latest_activity,
                                         view_revealed_list)
from luckycommon.strategy import handler as strategy_handler

from luckycommon.utils.api import token_required, filter_apples, filter_gp
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import (ParamError, AuthenticateError,
                                          ResourceInsufficient)

from future.utils import raise_with_traceback

from django.conf import settings
from django.views.decorators.http import require_GET, require_POST


_LOGGER = logging.getLogger('lucky')

DEBUG_USER = settings.DEBUG_USER


@require_GET
@response_wrapper
def get_activity_detail(request, activity_id):
    """
    get activity detail
    """
    activity_detail = view_activity_detail(
        request.user_id, activity_id, use_cache=True)
    return activity_detail


@require_GET
@response_wrapper
def get_activity_revealed(request, activity_id):
    """
    查看商品的中奖信息
    """
    activity_revealed = view_activity_revealed(activity_id)
    return activity_revealed


@require_GET
@response_wrapper
def get_latest_activity(request, template_id):
    """
    查看最新一期商品详情
    """
    lite_only = int(request.GET.get('lite_only', 0))
    activity_detail = view_latest_activity(
        request.user_id, template_id, lite_only=lite_only)
    return activity_detail


@require_GET
@response_wrapper
def get_last_revealed(request, template_id):
    """
    往期揭晓
    get last winner of template
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except Exception as e:
        raise_with_traceback(ParamError(e))
    revealed_list, count = view_revealed_list(
        page, size, template_id, use_cache=True)
    data = {
        'list': revealed_list,
        'page': page if page > 0 else 1,
        'size': len(revealed_list),
        'total_count': count
    }
    return data


@require_GET
@response_wrapper
@token_required
def get_my_activitys(request):
    """
    查看我的夺宝记录
    """
    user_id = request.user_id
    if not user_id:
        raise AuthenticateError('not login')

    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        only_win = int(request.GET['win']) if request.GET.get('win') else 0
        status = int(request.GET['status']) if request.GET.get(
            'status') else None
    except Exception as e:
        raise_with_traceback(ParamError(e))

    a_list, count = view_my_activitys_v2(user_id, page, size, only_win, status)
    data = {
        'list': a_list,
        'page': page if page > 0 else 1,
        'size': size if size else count,
        'total_count': count
    }
    return data


@require_GET
@response_wrapper
def get_other_activitys(request, user_id):
    """
    查看他人夺宝记录
    """
    try:
        user_id = int(user_id)
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        only_win = int(request.GET['win']) if request.GET.get('win') else 0
        status = int(request.GET['status']) if request.GET.get(
            'status') else None
    except Exception as e:
        raise_with_traceback(ParamError(e))

    a_list, count = view_other_activitys(user_id, page, size, only_win, status)
    a_list = filter_apples(request, a_list)
    a_list = filter_gp(request, a_list)
    data = {
        'list': a_list,
        'total_count': count
    }
    return data


@require_GET
@response_wrapper
@token_required
def get_activity_announce(request, activity_id):
    if request.user_id != DEBUG_USER:
        raise AuthenticateError()
    data = strategy_handler.fetch_announce_result(activity_id)
    return data
