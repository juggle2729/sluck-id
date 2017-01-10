# -*- coding: utf-8 -*-

import logging

from luckycommon.campaign.db.quiz import get_quiz, update_quiz_status, create_quiz
from luckycommon.campaign.model.quiz import QuizStatus, REWARD_AMOUNT
from luckycommon.db.transaction import add_system_award_transaction

_LOGGER = logging.getLogger('lucky')


def get_quiz_status(user_id):
    quiz = get_quiz(user_id)
    if not quiz:
        return -1
    return quiz.status


def create_quiz_store(user_id):
    create_quiz(user_id)


def mark_quiz_pass(user_id):
    quiz = update_quiz_status(user_id, QuizStatus.NOT_PASS.value, QuizStatus.PASSED.value)
    if quiz:
        add_system_award_transaction(user_id, REWARD_AMOUNT, u'Đố vui trúng thưởng')
        _LOGGER.info('send %s coin to user: %s, for pass the quiz' % (REWARD_AMOUNT, user_id))
