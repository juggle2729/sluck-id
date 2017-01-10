# -*- coding: utf-8 -*-
import logging

from django.views.decorators.http import require_POST, require_GET

from luckycommon.utils.api import token_required

from luckycommon.utils.decorator import response_wrapper
from luckycommon.level import handler as level_handler
from luckycommon.utils.exceptions import ParamError

_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
@token_required
def get_my_level(req):
    return level_handler.get_level_dict(int(req.user_id))


@require_POST
@response_wrapper
@token_required
def activate_coupon(req):
    try:
        level = int(req.POST.get('level'))
    except:
        raise ParamError('parameter `level` invalid')
    if level_handler.is_coupon_available(int(req.user_id), level):
        level_handler.activate_coupon(int(req.user_id), level)
        return {}
    else:
        raise ParamError('coupon not available')


@require_GET
@response_wrapper
def get_level_rank(req):
    rank_list = level_handler.get_rank()
    return {'list': rank_list,
            'count': len(rank_list)}


@require_GET
@response_wrapper
def get_level_week_rank(req):
    year = req.GET.get('year')
    week = req.GET.get('week')
    if week and year:
        rank_list = level_handler.get_week_rank(int(year), int(week))
    else:
        rank_list = level_handler.get_current_week_rank()
    return {'list': rank_list,
            'count': len(rank_list)}


@require_GET
@response_wrapper
def get_level_week_rank_list(req):
    rank_list = level_handler.get_week_rank_list()
    return {'list': rank_list,
            'count': len(rank_list)}
