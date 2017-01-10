# -*- coding: utf-8 -*-

from luckycommon.model import orm
from enum import Enum


REWARD_AMOUNT = 1


class QuizStatus(Enum):
    NOT_PASS = 0
    PASSED = 1


class Quiz(orm.Model):
    """
    夺宝测试
    """
    __tablename__ = "quiz"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    status = orm.Column(orm.Integer, default=0)
    reward = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
