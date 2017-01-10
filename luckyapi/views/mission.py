# -*- coding: utf-8 -*-
import json
import logging

from django.views.decorators.http import require_GET, require_POST

from luckycommon.mission import fresh_mission
from luckycommon.utils.api import token_required
from luckycommon.utils.exceptions import ParamError
from luckycommon.utils.decorator import response_wrapper


_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
@token_required
def get_status(request, mission_id):
    """
    获取任务进展
    """
    if mission_id == '10010':
        fresh_status = fresh_mission.get_step_status(request.user_id)
        return fresh_status
    raise ParamError('mission id invalid')


@require_GET
@response_wrapper
@token_required
def check_step(request, mission_id, step_id):
    """
    check任务
    """
    if mission_id == '10010' and step_id == '1':
        fresh_mission.check_step_a(request.user_id)
        return {}
    raise ParamError('mission id invalid')


@require_POST
@response_wrapper
@token_required
def activate(request, mission_id):
    """
    激活任务(完成后)
    """
    if mission_id == '10010':
        fresh_mission.activate(request.user_id)
        return {}
    raise ParamError('mission id invalid')
