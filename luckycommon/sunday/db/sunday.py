# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from luckycommon.model import orm
from luckycommon.sunday.model.sunday import *
from luckycommon.utils.decorator import sql_wrapper

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_apply(user_id, term_id):
    return SundayApply.query.filter(SundayApply.term_id == term_id)\
                      .filter(SundayApply.user_id == user_id).first()


@sql_wrapper
def apply_user(user_id, term_id):
    sunday_apply = SundayApply.query.filter(SundayApply.user_id == user_id)\
                              .filter(SundayApply.term_id == term_id).first()
    if not sunday_apply:
        sunday_apply = SundayApply()
        sunday_apply.user_id = user_id
        sunday_apply.term_id = term_id
        sunday_apply.save()
    return sunday_apply
    

@sql_wrapper
def get_applys_by_term(term_id):
    return SundayApply.query.filter(SundayApply.term_id == term_id).all()


@sql_wrapper
def create_first_record(user_id, activity_id, consume_amount, first_amount):
    record = SundayRecord()
    record.activity_id = activity_id
    record.user_id = user_id
    record.return_amount = consume_amount
    record.first_amount = first_amount
    record.save()


@sql_wrapper
def get_records_by_activity(activity_id):
    return SundayRecord.query.filter(SundayRecord.activity_id == activity_id).all()


@sql_wrapper
def update_second_record(record_id, second_amount):
    SundayRecord.query.filter(SundayRecord.id == record_id).update({
        'second_amount': second_amount,
        'updated_at': datetime.utcnow()
    })
    orm.session.commit()
