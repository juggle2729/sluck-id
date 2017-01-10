# -*- coding: utf-8 -*-
import json
import logging

from django.views.decorators.http import require_GET

from luckyapi.logic.scrolling import view_scrolling, view_lucky_wall, view_horn
from luckycommon.utils.decorator import response_wrapper


_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
def fetch_scrolling(req):
    """
    获取跑马灯
    eg:
    {
        'size': 10,
        'list': [
            {
                'text': u'恭喜大白菜1分钟之前获得小米Note2',
                'cmd': '0#'
            }
        ]
    }
    """
    scrolling_list = view_scrolling()
    data = {
        'size': len(scrolling_list),
        'list': scrolling_list
    }
    return data


@require_GET
@response_wrapper
def fetch_wall(req):
    """
    获取幸运墙
    """
    wall_list = view_lucky_wall()
    data = {
        'list': wall_list
    }
    return data


@require_GET
@response_wrapper
def fetch_horn(req):
    """
    获取大喇叭
    """
    horn_list = view_horn()
    data = {
        'list': horn_list
    }
    return data
