# -*- coding: utf-8 -*-
import logging

from django.views.decorators.http import require_GET, require_POST

from luckyapi.logic.crowdfunding import view_latest_activity
from luckycommon.campaign import (recharge_campaign,
                                  new_recharge_campaign,
                                  daily_buy_campaign,
                                  moist_campaign,
                                  god_campaign,
                                  first_double,
                                  miss_return,
                                  recommend_campaign)
from luckycommon.campaign.quiz_controller import get_quiz_status, mark_quiz_pass, create_quiz_store
from luckycommon.model.campaign import CAMPAIGN_DICT, CAMPAIGN_TYPE
from luckycommon.sunday import handler as sunday_handler
from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError, ResourceNotFound
from luckycommon.zero import handler as zero_handler


_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
def campaign_award_timeline(request, campaign_id):
    """
    获取活动奖励的时间线
    """
    if campaign_id not in CAMPAIGN_DICT:
        raise ParamError('campaign id invalid')
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if campaign_info['type'] == CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN:
        timeline_info = new_recharge_campaign.get_award_timeline(campaign_id)
    else:
        raise ParamError('campaign not support')
    return timeline_info


@require_GET
@response_wrapper
@token_required
def fetch_user_achievement(request, campaign_id):
    """
    获取用户的活动成就
    """
    if campaign_id not in CAMPAIGN_DICT:
        raise ParamError('campaign id invalid')
    user_id = request.user_id
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if campaign_info['type'] == CAMPAIGN_TYPE.RECHARGE_CAMPAIGN:
        current_amount, level_list = recharge_campaign.get_reached_levels(user_id, campaign_id) 
    elif campaign_info['type'] == CAMPAIGN_TYPE.DAILY_BUY_CAMPAIGN:
        current_amount, level_list = daily_buy_campaign.get_reached_levels(user_id, campaign_id) 
    elif campaign_info['type'] == CAMPAIGN_TYPE.MOIST_CAMPAIGN:
        applied = moist_campaign.get_campaign_status(user_id, campaign_id)
        data = {
            'applied': applied
        }
        return data
    elif campaign_info['type'] == CAMPAIGN_TYPE.WEALTH_GOD_CAMPAIGN:
        god_campaign_item = god_campaign.get_campaign_status(user_id)
        data = fill_god_campaign_response(user_id, god_campaign_item)
        return data
    elif campaign_info['type'] == CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN:
        level_list = new_recharge_campaign.get_reached_levels(user_id, campaign_id)
        return {
            'level_list': level_list
        }
    else:
        raise ParamError('campaign not support')
    data = {
        'current_amount': current_amount,
        'level_list': level_list
    }
    return data


def fill_god_campaign_response(user_id, item):
    if not item:
        return {
            'activity_list': [],
            'level_list': [],
            'fresh_times': 0
        }
    a_list = []
    winned_tids = [] if not item.winned_tids else item.winned_tids.split(',')
    first_activity = view_latest_activity(user_id, item.first_tid, lite_only=True)
    if str(item.first_tid) in winned_tids:
        first_activity.update({'has_winned': True})
    a_list.append(first_activity)

    second_activity = view_latest_activity(user_id, item.second_tid, lite_only=True)
    if str(item.second_tid) in winned_tids:
        second_activity.update({'has_winned': True})
    a_list.append(second_activity)

    third_activity = view_latest_activity(user_id, item.third_tid, lite_only=True)
    if str(item.third_tid) in winned_tids:
        third_activity.update({'has_winned': True})
    a_list.append(third_activity)

    level_list = [{
        'level': 1,
        'status': item.first_blood,
    },{
        'level': 2,
        'status': item.double_kill,
    },{
        'level': 3,
        'status': item.triple_kill,
    }]
    return {
        'activity_list': a_list,
        'level_list': level_list,
        'fresh_times': item.fresh_times
    }


@require_POST
@response_wrapper
@token_required
def activate_user_achievement(request, campaign_id, level_id):
    """
    激活用户的活动成就(拆开红包/分享)
    """
    try:
        level_id = int(level_id)
    except:
        raise ParamError('level id invalid')
    if campaign_id not in CAMPAIGN_DICT:
        raise ParamError('campaign id invalid')
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    if campaign_info['type'] == CAMPAIGN_TYPE.RECHARGE_CAMPAIGN:
        coupon_list = recharge_campaign.activate_level(request.user_id, campaign_id, level_id)
        coupon_list = [{
                          'id': coupon.id,
                          'title': coupon.title, 
                          'desc': coupon.desc, 
                          'price': coupon.price
                       } for coupon in coupon_list]
        data = {
            'coupon_list': coupon_list
        }
        return data
    elif campaign_info['type'] == CAMPAIGN_TYPE.WEALTH_GOD_CAMPAIGN:
        coupon_list = god_campaign.activate_level(request.user_id, level_id)
        coupon_list = [{
                          'id': coupon.id,
                          'title': coupon.title, 
                          'desc': coupon.desc, 
                          'price': coupon.price
                       } for coupon in coupon_list]
        data = {
            'coupon_list': coupon_list
        }
        return data
    elif campaign_info['type'] == CAMPAIGN_TYPE.DAILY_BUY_CAMPAIGN:
        group_coupon = daily_buy_campaign.activate_level(request.user_id, campaign_id, level_id)
        data = {
            'coupon_id': group_coupon.id,
            'total_count': group_coupon.total_count
        }
        return data
    elif campaign_info['type'] == CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN:
        double_kill, coupon_list = new_recharge_campaign.activate_level(request.user_id, campaign_id, level_id)
        update_list = []
        coupon_dict = {}
        for coupon in coupon_list:
            tid = coupon.template_id
            coupon_dict.setdefault(tid, {
                'id': coupon.id,
                'title': coupon.title, 
                'desc': coupon.desc, 
                'price': coupon.price,
                'count': 0
            })
            coupon_dict[tid]['count'] += 1
        update_list = [coupon_dict[tid] for tid in coupon_dict]
        data = {
            'coupon_list': update_list,
            'double_kill': double_kill
        }
        return data
    else:
        raise ParamError('campaign not support')


@require_POST
@response_wrapper
@token_required
def fresh_god(request):
    """
    刷新财神指路推荐列表
    """
    user_id = request.user_id
    new_item = god_campaign.fresh(user_id)
    data = fill_god_campaign_response(user_id, new_item)
    return data


@require_GET
@response_wrapper
def recommend_award_timeline(request, campaign_name):
    """
    获取推荐活动的时间线
    """
    user_id = request.user_id
    a_list = recommend_campaign.get_award_timeline(campaign_name)
    return {
        'list': a_list
    }


@require_GET
@response_wrapper
def recommend_campaign_fresh(request, campaign_name):
    """
    获取推荐活动的配置
    """
    user_id = request.user_id
    group = recommend_campaign.fresh(campaign_name)
    return {
        'list': group
    }


@require_GET
@response_wrapper
@token_required
def recommend_coupon_status(request, campaign_name):
    """
    推荐活动状态
    """
    user_id = request.user_id
    status = recommend_campaign.get_status(user_id, campaign_name)
    data = {
        'activated': True if status else False
    }
    return data


@require_POST
@response_wrapper
@token_required
def fetch_recommend_coupon(request, campaign_name):
    """
    领取推荐活动红包(每日领取)
    """
    user_id = request.user_id
    coupon_list = recommend_campaign.activate(user_id, campaign_name)
    coupon_list = [{
                      'id': coupon.id,
                      'title': coupon.title, 
                      'desc': coupon.desc, 
                      'price': coupon.price
                   } for coupon in coupon_list]
    return {
        'coupon_list': coupon_list
    }


@require_GET
@response_wrapper
def fresh_zero(request):
    """
    获取0元购定时活动状态(客户端首页倒计时)
    """
    user_id = request.user_id
    data = zero_handler.get_zero_status(user_id)
    return data


@require_POST
@response_wrapper
@token_required
def share_zero(request):
    """
    分享0元购定时活动
    """
    user_id = request.user_id
    try:
        template_id = int(request.POST.get('gid'))
        term_number = int(request.POST.get('term_number'))
    except:
        raise ParamError('param error')
    zero_handler.submit_share(user_id, template_id, term_number)
    return {}


@require_POST
@response_wrapper
@token_required
def zero_push(request):
    """
    0元购活动提醒开关
    """
    user_id = request.user_id
    try:
        push_open = int(request.POST.get('open', 0))
    except:
        raise ParamError('param error')
    zero_handler.set_push(user_id, push_open)
    return {}


@require_POST
@response_wrapper
@token_required
def sunday_apply(request):
    """
    周日活动报名
    """
    user_id = request.user_id
    sunday_handler.apply_sunday(user_id)
    return {}


@require_GET
@response_wrapper
def fresh_sunday(request):
    """
    获取周日活动状态
    """
    user_id = request.user_id
    data = sunday_handler.get_sunday_status(user_id)
    if not data:
        raise ResourceNotFound()
    return data


@require_GET
@response_wrapper
@token_required
def first_double_status(request):
    """
    获取首充翻倍状态
    """
    user_id = request.user_id
    status = first_double.get_status(user_id)
    return status


@require_POST
@response_wrapper
@token_required
def first_double_apply(request):
    """
    首充翻倍活动报名
    """
    user_id = request.user_id
    first_double.apply(user_id)
    return {}


@require_GET
@response_wrapper
def miss_return_status(request):
    """
    获取不中包赔状态
    """
    user_id = request.user_id
    return miss_return.get_status(user_id)


@require_GET
@response_wrapper
@token_required
def quiz_status(request):
    user_id = request.user_id
    status = get_quiz_status(user_id)
    return {'is_pass': status}


@require_POST
@response_wrapper
@token_required
def submit_quiz(request):
    try:
        is_pass = int(request.POST.get('is_pass'))
        user_id = request.user_id
    except:
        raise ParamError('parameter invalid')
    create_quiz_store(user_id)
    if is_pass == 1:
        mark_quiz_pass(user_id)
    return {}
