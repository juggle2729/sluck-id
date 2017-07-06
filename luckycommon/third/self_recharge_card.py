# -*- coding: utf-8 -*-
import logging

from luckyapi.logic.recharge_card import consume_recharge_card
from luckycommon.async.async_job import track_one, increment_user
from luckycommon.credit.db.credit import add_special_recharge_award_credit
from luckycommon.db.pay import update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.utils.exceptions import RechargeCardError
from luckycommon.utils.respcode import StatusCode

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')
_AWARD_CREDIT_UNIT = 50


def pay_via_self_recharge_card(pay, card_id, card_secret):
    pay_id = pay.id
    user_id = pay.user_id
    card = consume_recharge_card(user_id, pay_id, card_id, card_secret)
    extend = {
        'title': u'recharge card',
        'ext': {
            'pay_id': pay_id,
            'card_info': {
                'card_id': card_id,
                'card_secret': card_secret
            }
        }
    }
    if card:
        total_fee = card.amount
        update_pay_ext(pay_id, extend['ext'])
        res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
        add_special_recharge_award_credit(user_id, total_fee * _AWARD_CREDIT_UNIT)
        if res:
            track_one.delay('recharge', {'price': float(total_fee), 'channel': 'coda'}, user_id)
            increment_user.delay(user_id, 'total_recharge', total_fee)
            _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                           'price': total_fee,
                           'channel': 'coda'})
            try:
                pay_after_recharge(pay)
            except Exception as e:
                raise RechargeCardError(status=StatusCode.SERVER_ERROR)
        return True
    else:
        add_pay_fail_transaction(user_id, pay_id, None, extend)
        raise RechargeCardError(status=StatusCode.SERVER_ERROR)
