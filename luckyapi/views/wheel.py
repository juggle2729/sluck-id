# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.campaign import fortune_wheel

from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError

from django.conf import settings
from django.views.decorators.http import require_GET, require_POST

from future.utils import raise_with_traceback


_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
def get_timeline(request):
    """
    获取活动奖励的时间线
    """
    a_list = fortune_wheel.get_timeline()
    return {
        'list': a_list
    }


@require_GET
@response_wrapper
@token_required
def get_award_list(request):
    """
    获取用户中奖列表
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    user_id = request.user_id
    a_list = fortune_wheel.get_user_award(user_id, page, size)
    return {
        'list': a_list
    }


@require_GET
@response_wrapper
@token_required
def get_wheel_status(request):
    """
    获取用户的转盘状态
    """
    user_id = request.user_id
    return fortune_wheel.get_status(user_id)


@require_POST
@response_wrapper
@token_required
def play_wheel(request):
    """
    摇奖
    """
    user_id = request.user_id
    award_index = fortune_wheel.single_play(user_id)
    return {
        'award_index': award_index
    }
