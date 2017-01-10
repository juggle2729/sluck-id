# -*- coding: utf-8 -*-
import logging

from luckycommon.area import handler as area_handler

from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError

from django.views.decorators.http import require_GET

_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
@token_required
def get_regions(request):
    try:
        parent_id = long(request.GET.get('area_id'))
    except:
        raise ParamError('area id invalid')
    parent_id = str(parent_id)
    if len(parent_id) > 9:
        raise ParamError('area id invalid')
    area_list = area_handler.get_list_by_parent(parent_id)
    _LOGGER.info('%s requested %s area data', request.user_id, len(area_list))
    data = {
        'regions': area_list
    }
    return data
