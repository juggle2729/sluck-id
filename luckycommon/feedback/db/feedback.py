# -*- coding: utf-8 -*-
import logging

from luckycommon.feedback.model.feedback import *

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def submit(qq, content, chn, cvc, user_id=None, nick_name=None, phone=None):
    feedback = Feedback()
    feedback.chn = chn
    feedback.cvc = cvc
    feedback.qq = qq
    feedback.content = content
    if user_id:
        feedback.user_id = user_id
    if nick_name:
        feedback.nick_name = nick_name
    if phone:
        feedback.phone = phone
    feedback.save()


@sql_wrapper
def list_feedback(query_dct):
    return list_object(query_dct, Feedback)
