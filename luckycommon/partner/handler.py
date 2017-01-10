# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.logic import coupon as coupon_handler

from luckycommon.cache import redis_cache
from luckycommon.campaign import fortune_wheel

from luckycommon.db import partner as partner_db
from luckycommon.account.db import account as account_db

from luckycommon.async import async_job

from luckycommon.utils.tz import utc_to_local
from luckycommon.utils.exceptions import ParamError


_LOGGER = logging.getLogger('lucky')

_DEFAULT_PAGE_SIZE = 20


def get_partners(user_id):
    """
    获取好友列表（邀请的用户）
    """
    # TODO: we can cache here
    first_partner_list = []
    second_partner_list = []
    first_list = partner_db.get_direct_partners(user_id)
    first_partner_list = first_list
    for uid in first_list:
        second_list = partner_db.get_direct_partners(uid)
        second_partner_list.extend(second_list)
    return first_partner_list, second_partner_list


def get_partner_reward_by_level(user_id):
    return (partner_db.get_reward_by_level(user_id, 1),
            partner_db.get_reward_by_level(user_id, 2))


def get_partner_coupon_status(user_id):
    partner_coupon = partner_db.init_coupon_status(user_id)
    return json.loads(partner_coupon.coupon_status)


def activate_coupon(user_id, level_id):
    return partner_db.activate_coupon(user_id, level_id)


def get_partner_reward_records(user_id, page, size):
    """
    获取好友充值返利的数据
    """
    revealed_list = []
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    reward_list = []
    record_items = partner_db.get_partner_rewards(user_id, limit, offset)
    for item in record_items:
        amount = item.amount
        reward_list.append({
            'reward_time': utc_to_local(item.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'partner_id': item.partner_id,
            'relation_level': item.relation_level,
            'amount': item.amount
        })
    return reward_list


def bind_inviter(user_id, inviter_id):
    # check circle
    my_item = partner_db.get_user_inviter(user_id)
    if my_item:
        raise ParamError('duplicate set')
    try:
        inviter_id = int(inviter_id)
    except:
        raise ParamError('inviter id invalid')
    inviter_account = account_db.get_account(inviter_id)
    if inviter_id == user_id or not inviter_account:
        raise ParamError('invalid inviter')
    inviter_item = partner_db.get_user_inviter(inviter_id)
    invite_list = [str(inviter_id)]
    if inviter_item:
        invite_list.extend(inviter_item.invite_list.split(','))
        if str(user_id) in invite_list:
            _LOGGER.warn('found inviter circle, %s, %s', user_id, inviter_id)
            raise ParamError('circle invite')
    async_job.create_partner_relation.delay(user_id, invite_list)
    # award coupon
    coupon_handler.send_coupon_to_user(user_id, 136, 1)  # 拜师红包，满5减1
    coupon_handler.send_coupon_to_user(user_id, 137, 1)  # 拜师红包，满10减2
    fortune_wheel.callback_task(inviter_id, 4)
    try:
        partner_db.update_coupon_status(inviter_id)
    except:
        pass


def bind_inviter_by_track(user_id, track_key):
    inviter_id = redis_cache.get_inviter_track(track_key)
    if inviter_id:
        _LOGGER.info('%s bind inviter %s by track', user_id, inviter_id)
        bind_inviter(user_id, inviter_id)
    return inviter_id


def track_inviter(track_key, inviter_id):
    # check inviter
    inviter_account = account_db.get_account(inviter_id)
    if not inviter_account:
        raise ParamError('invalid inviter')
    redis_cache.set_inviter_track(track_key, inviter_id)
