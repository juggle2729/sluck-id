# -*- coding: utf-8 -*-
import logging

from luckyapi.logic import coupon as coupon_handler

from luckycommon.model.mission import FreshMission
from luckycommon.db.mission import FreshMissionDb


_LOGGER = logging.getLogger('lucky')


def check_step_a(user_id):
    """
    了解一元购
    """
    try:
        FreshMissionDb.check_step_a(user_id)
    except Exception as e:
        _LOGGER.exception('fresh_mission, check_step_a exception:%s', e)


def check_step_b(user_id):
    """
    完善个人资料
    """
    try:
        FreshMissionDb.check_step_b(user_id)
    except Exception as e:
        _LOGGER.exception('fresh_mission, check_step_b exception:%s', e)


def check_step_c(user_id):
    """
    完成签到
    """
    try:
        FreshMissionDb.check_step_c(user_id)
    except Exception as e:
        _LOGGER.exception('fresh_mission, check_step_c exception:%s', e)


def check_step_d(user_id):
    """
    成功充值
    """
    try:
        FreshMissionDb.check_step_d(user_id)
    except Exception as e:
        _LOGGER.exception('fresh_mission, check_step_d exception:%s', e)


def get_step_status(user_id):
    status_dict = {
        'step_a': 0,
        'step_b': 0,
        'step_c': 0,
        'step_d': 0,
        'activated': 0
    }
    status_item = FreshMissionDb.get_step_status(user_id)
    if status_item:
       status_dict.update({'step_a': status_item.step_a})
       status_dict.update({'step_b': status_item.step_b})
       status_dict.update({'step_c': status_item.step_c})
       status_dict.update({'step_d': status_item.step_d})
       status_dict.update({'activated': status_item.status})
    return status_dict


def activate(user_id):
    FreshMissionDb.activate(user_id)
    coupon_handler.send_coupon_to_user(user_id, 138, 1)  # 新手任务红包，满2减1


def query_tips(user_id):
    status_item = FreshMissionDb.get_step_status(user_id)
    if (status_item and status_item.step_a == 1 and
        status_item.step_b == 1 and
        status_item.step_c == 1 and
        status_item.step_d == 1 and
        status_item.status == 0):
        return 1
    return 0


def check_complete(user_id):
    item = FreshMissionDb.get_step_status(user_id)
    return True if item and item.status else False
