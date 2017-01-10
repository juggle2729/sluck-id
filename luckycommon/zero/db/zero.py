# -*- coding: utf-8 -*-
import logging

from luckycommon.zero.model.zero import ZeroShare, ZeroPush
from luckycommon.utils.decorator import sql_wrapper

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_share(user_id, template_id, term_number):
    return ZeroShare.query.filter(ZeroShare.user_id == user_id)\
                    .filter(ZeroShare.template_id == template_id)\
                    .filter(ZeroShare.term_number == term_number).first()


@sql_wrapper
def submit_share(user_id, template_id, term_number):
    item = ZeroShare.query.filter(ZeroShare.user_id == user_id)\
                    .filter(ZeroShare.template_id == template_id)\
                    .filter(ZeroShare.term_number == term_number)\
                    .with_lockmode('update').first()
    if not item:
        item = ZeroShare()
        item.user_id = user_id
        item.template_id = template_id
        item.term_number = term_number
        item.share_times = 1
        item.save()
    else:
        item.share_times += 1
        item.save()


@sql_wrapper
def set_push(user_id, push_open):
    item = ZeroPush.query.filter(ZeroPush.user_id == user_id).first()
    if not item and push_open == 1:
        item = ZeroPush()
        item.user_id = user_id
        item.need_push = 1
        item.save()
    elif item:
        item.need_push = 1 if push_open >= 1 else 0
        item.save()


@sql_wrapper
def get_push(user_id):
    return ZeroPush.query.filter(ZeroPush.user_id == user_id).first()
