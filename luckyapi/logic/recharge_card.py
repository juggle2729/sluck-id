# -*- coding: utf-8 -*-
import random
import string
from datetime import datetime

from django.contrib.auth.hashers import make_password, check_password

from luckycommon.model import orm
from luckycommon.model.recharge_card import RechargeCard, RECHARGE_CARD_SECRET_LENGTH, RechargeCardStatus
from luckycommon.utils.exceptions import RechargeCardError
from luckycommon.utils.respcode import StatusCode


def _gen_random_string(count):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(count))


def create_recharge_card(amount, agent=None):
    card = RechargeCard()
    raw_secret = _gen_random_string(RECHARGE_CARD_SECRET_LENGTH)
    card.secret = make_password(raw_secret)
    card.amount = amount
    card.status = RechargeCardStatus.VALID.value
    if agent:
        card.agent = agent
    card.save()
    return card.id, raw_secret


def get_card_by_id(card_id):
    card = RechargeCard.query.filter(RechargeCard.id == card_id).first()
    return card


def get_self_recharge_card_status(card_id):
    card = RechargeCard.query.filter(RechargeCard.id == card_id).first()
    if not card:
        return 'not_found'
    return card.status


def consume_recharge_card(user_id, pay_id, card_id, card_secret):
    card = RechargeCard.query.filter(RechargeCard.id == card_id).first()
    if not card:
        raise RechargeCardError(status=StatusCode.CARD_NOT_FOUND)

    if card.status == RechargeCardStatus.USED.value:
        raise RechargeCardError(status=StatusCode.USED_CARD)

    if card.status == RechargeCardStatus.INVALID.value:
        raise RechargeCardError(status=StatusCode.INVALID_CARD)

    encoded_secret = card.secret
    if not check_password(card_secret, encoded_secret):
        raise RechargeCardError(status=StatusCode.WRONG_SECRET)

    session = orm.session
    try:
        result = RechargeCard.query.filter(RechargeCard.id == card_id).filter(RechargeCard.status == RechargeCardStatus.VALID.value).update(
            {
                'status': RechargeCardStatus.USED.value,
                'user_id': user_id,
                'pay_id': pay_id,
                'updated_at': datetime.utcnow()
            })
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

    if result:
        return card
    else:
        raise RechargeCardError(status=StatusCode.SERVER_ERROR)
