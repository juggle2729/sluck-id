# -*- coding: utf-8 -*-
import logging

from luckycommon.cache import redis_cache
from luckycommon.credit.db import credit as credit_db
from luckycommon.db import partner as partner_db

_LOGGER = logging.getLogger('lucky')


def reward_inviters(user_id, recharge_amount):
    try:
        inviter_item = partner_db.get_user_inviter(user_id)
        if inviter_item:
            invite_list = inviter_item.invite_list.split(',')
            valid_list = invite_list[:2]
            (first_inviter,
             second_inviter) = valid_list + (2 - len(valid_list)) * [None]
            if first_inviter:
                # 40
                award_credit = 40 * recharge_amount
                credit_db.add_credit(first_inviter, award_credit, u"Đối tác nhận thưởng")
                partner_db.add_reward_record(first_inviter, user_id, 1, award_credit)
                _LOGGER.info('reward inviter %s %s credit', first_inviter, award_credit)
                redis_cache.set_user_pending(first_inviter, 'partner_reward', 1)
            if second_inviter:
                # 20
                award_credit = 20 * recharge_amount
                credit_db.add_credit(second_inviter, award_credit, u"Đối tác nhận thưởng")
                partner_db.add_reward_record(second_inviter, user_id, 2, award_credit)
                _LOGGER.info('reward inviter %s %s credit', second_inviter, award_credit)
                redis_cache.set_user_pending(second_inviter, 'partner_reward', 1)
    except Exception as e:
        _LOGGER.exception('reward_inviters exception:%s', e)
