# -*- coding: utf-8 -*-
import json
import logging
import datetime

from luckycommon.mission import fresh_mission
from luckycommon.campaign import fortune_wheel
from luckycommon.cache import redis_cache

from luckycommon.credit.db import credit as credit_db
from luckycommon.credit.model.check import CHECK_TYPE, DAILY_SIGN_AWARDS

from luckycommon.social import handler as social_handler

from luckycommon.utils.api import token_required
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.decorator import response_wrapper
from django.views.decorators.http import require_POST, require_GET


_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
@token_required
def sign_status(request):
    """
    签到状态 
    """
    user_id = request.user_id
    today_checks = credit_db.get_today_checks(request.user_id)
    today_sign = 0
    today_share = 0
    for check_item in today_checks:
        if check_item.check_type == CHECK_TYPE.DAILY_SIGN:
            today_sign += check_item.check_times
        if check_item.check_type == CHECK_TYPE.DAILY_SHARE:
            today_share += check_item.check_times
    account_sign = credit_db.get_user_sign(request.user_id)
    continuous_times = 1 if not account_sign else account_sign.continuous_times
    if not today_sign:
        today = datetime.datetime.strptime(utc_to_local_str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S')
        last_sign_at = None if not account_sign else account_sign.last_sign_at
        if last_sign_at:
            timedelta = (today.replace(hour=0, minute=0, second=0, microsecond=0) -
                last_sign_at.replace(hour=0, minute=0, second=0, microsecond=0))
            if timedelta == datetime.timedelta(1):
                continuous_times += 1
            else:
                continuous_times = 1
        else:
            continuous_times = 1
    if continuous_times == 1:
        added_credit = DAILY_SIGN_AWARDS[0]
    elif continuous_times == 2:
        added_credit = DAILY_SIGN_AWARDS[1]
    elif continuous_times >= 2:
        added_credit = DAILY_SIGN_AWARDS[2]
    return {
        'checked': today_sign,
        'added_credit': added_credit
    }


@require_POST
@response_wrapper
@token_required
def check_sign(request):
    """
    签到
    """
    user_id = request.user_id
    added_credit = credit_db.daily_check(user_id, CHECK_TYPE.DAILY_SIGN)
    account_sign = credit_db.get_user_sign(user_id)
    continuous_times = 0 if not account_sign else account_sign.continuous_times 
    fresh_mission.check_step_c(user_id)
    fortune_wheel.callback_task(user_id, 0)
    # add credit pool
    redis_cache.add_credit_pool(user_id, added_credit)
    return {
        'added_credit': added_credit,
        'continuous_times': continuous_times
    }


@require_POST
@response_wrapper
@token_required
def check_share(request):
    """
    每日分享，分享成功后调用
    """
    added_credit = credit_db.daily_check(request.user_id, CHECK_TYPE.DAILY_SHARE)
    return {
        'added_credit': added_credit
    }


@require_POST
@response_wrapper
@token_required
def submit_share(request):
    """
    每日分享，分享前调用
    """
    user_id = request.user_id
    share_type = int(request.POST.get('share_type', 0))
    share_extend = social_handler.submit_share(user_id, share_type)
    return {
        'extend': share_extend
    }
