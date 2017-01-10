# -*- coding: utf-8 -*-
import logging

from django.views.decorators.http import require_GET

from luckyapi.logic.crowdfunding import view_activitys

from luckycommon.utils.api import filter_apples, filter_gp
from luckycommon.utils.exceptions import ParamError
from luckycommon.utils.decorator import response_wrapper

from django.conf import settings


_LOGGER = logging.getLogger('lucky')

DEFAULT_SIZE = 7


@require_GET
@response_wrapper
def recommend_activitys(request):
    """
    获取推荐活动列表 
    """
    scene_id = int(request.GET.get('scene_id', 2))
    if scene_id == 1:
        # 中奖纪录为空
        activitys, count = view_activitys(page=1, size=DEFAULT_SIZE, sort_id=5)
    elif scene_id == 2:
        # 清单为空
        activitys, count = view_activitys(page=1, size=DEFAULT_SIZE, sort_id=1)
    elif scene_id == 3:
        # 夺宝记录为空
        activitys, count = view_activitys(page=1, size=DEFAULT_SIZE, sort_id=1)
    elif scene_id == 4:
        # 新用户引导推荐——最易中
        pass
    elif scene_id == 5:
        # 新用户引导推荐——最热门
        pass
    else:
        raise ParamError('scene id invalid')
    activitys = filter_apples(request, activitys)
    activitys = filter_gp(request, activitys)
    data = {
        'list': activitys,
    }
    return data


@require_GET
@response_wrapper
def recommend_fresh(request):
    """
    新手引导推荐
    """
    data = {
        'list': settings.FRESH_RECOMMEND,
    }
    return data
