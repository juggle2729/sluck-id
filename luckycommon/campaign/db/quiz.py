# -*- coding: utf-8 -*-

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.campaign.model.quiz import Quiz, QuizStatus


@sql_wrapper
def get_quiz(user_id):
    quiz = Quiz.query.filter(Quiz.user_id == user_id).first()
    return quiz


@sql_wrapper
def create_quiz(user_id):
    quiz = Quiz.query.filter(Quiz.user_id == user_id).first()
    if not quiz:
        quiz = Quiz()
        quiz.user_id = user_id
        quiz.save()
    return quiz


@sql_wrapper
def update_quiz_status(user_id, origin, final):
    quiz = Quiz.query.filter(Quiz.user_id == user_id).filter(Quiz.status == origin).with_lockmode('update').first()
    if not quiz:
        return None
    quiz.status = final
    quiz.save()
    return quiz


