# -*- coding: utf-8 -*-
import json
import random
import logging
import hashlib

from luckycommon.cache import redis_cache

from luckycommon.partner import handler as partner_handler
from luckycommon.utils.tz import now_ts
from luckycommon.utils.api import token_required, get_client_ip, get_client_ua
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError

from django.views.decorators.http import require_GET, require_POST

_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
def track_inviter(request):
    """
    track邀请者
    """
    try:
        inviter_id = int(request.GET.get('uid', None))
        if not inviter_id:
            raise ParamError('uid invalid')
    except:
        raise ParamError('uid invalid')
    client_ip = get_client_ip(request)
    ua = get_client_ua(request)
    track_str = '%s' % (client_ip)
    # track_key = hashlib.md5(track_str).hexdigest()
    partner_handler.track_inviter(track_str, inviter_id)
    return {}


@require_POST
@response_wrapper
@token_required
def add_inviter(request):
    inviter_id = request.POST.get('inviter_id', None)
    if not inviter_id:
        raise ParamError('parameter inviter_id not found')
    partner_handler.bind_inviter(request.user_id, inviter_id)
    return {}


@require_GET
@response_wrapper
@token_required
def get_entry(request):
    user_id = request.user_id
    first_partners, _ = partner_handler.get_partners(user_id)
    first_reward, _ = partner_handler.get_partner_reward_by_level(user_id)
    data = {
        'invitation_code': str(user_id),
        'invitation_count': len(first_partners),
        'invitation_reward': first_reward
    }
    return data


@require_GET
@response_wrapper
@token_required
def reward_status(request):
    """
    获取当前好友充值返利情况
    """
    user_id = request.user_id
    (first_partners, second_partners) = partner_handler.get_partners(user_id)
    (first_reward, second_reward) = partner_handler.get_partner_reward_by_level(user_id)
    data = {
        'total': first_reward + second_reward,
        'partner_count': len(first_partners) + len(second_partners),
        'level_list': [{
            'level': 1,
            'member_count': len(first_partners),
            # 'credit_amount': first_reward,
        }, {
            'level': 2,
            'member_count': len(second_partners),
            # 'credit_amount': second_reward,
        }
        ]
    }
    redis_cache.clear_user_pending(user_id, 'partner_reward')
    return data


@require_GET
@response_wrapper
@token_required
def reward_record(request):
    """
    获取充值返利记录
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except:
        raise ParamError('param invalid')
    record_list = partner_handler.get_partner_reward_records(request.user_id, page, size)
    data = {
        'list': record_list
    }
    return data


@require_GET
@response_wrapper
def current_accumulation(request):
    """
    获取当前的累积数据
    """
    current_dict = redis_cache.get_current_partner_accu()
    last_ts = int(current_dict['ts'])
    member_count = int(current_dict['member_count'])
    price_amount = int(current_dict['price_amount'])
    now = now_ts()
    if last_ts + 3600 < now:
        # update
        add_member = random.randint(1, 100)
        add_price = random.randint(10, 8000)
        current_dict['member_count'] = member_count + add_member
        current_dict['price_amount'] = price_amount + add_price
        current_dict['ts'] = now
        redis_cache.set_current_partner_accu(current_dict)
    data = {
        'member_count': member_count,
        'price_amount': price_amount
    }
    return data


@require_GET
@response_wrapper
@token_required
def award_status(request):
    """
    获取充值返利奖励状态
    """
    user_id = request.user_id
    coupon_status = partner_handler.get_partner_coupon_status(user_id)
    return {
        'list': coupon_status
    }


@require_POST
@response_wrapper
@token_required
def activate_level(request, level_id):
    """
    领取师徒奖励红包
    """
    user_id = request.user_id
    try:
        level_id = int(level_id)
    except:
        raise ParamError('level id invalid')
    coupon = partner_handler.activate_coupon(user_id, level_id)
    return {
        'id': coupon.id,
        'title': coupon.title,
        'desc': coupon.desc,
        'price': coupon.price
    }
