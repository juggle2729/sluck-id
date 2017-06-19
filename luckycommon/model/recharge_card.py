# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.custom_enum import CustomEnum

ALLOWED_RECHARGE_CARD_AMOUNT = (50, 100, 250, 500)
RECHARGE_CARD_ID_LENGTH = 8
RECHARGE_CARD_SECRET_LENGTH = 8


class RechargeCardStatus(CustomEnum):
    VALID = 'valid'
    USED = 'used'
    INVALID = 'invalid'


class RechargeCard(orm.Model):
    __tablename__ = "recharge_card"
    id = orm.Column(orm.BigInteger, primary_key=True)
    secret = orm.Column(orm.VARCHAR)
    amount = orm.Column(orm.Integer)
    status = orm.Column(orm.VARCHAR)
    agent = orm.Column(orm.VARCHAR, default='official')
    user_id = orm.Column(orm.BigInteger)
    pay_id = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
