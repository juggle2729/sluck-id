# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.model.credit import RecordLite
from luckycommon.credit.db import credit as credit_db
from luckycommon.utils.tz import utc_to_local

from future.utils import raise_with_traceback

_LOGGER = logging.getLogger('lucky')

_DEFAULT_PAGE_SIZE = 20


def get_user_credit_records(user_id, page, size, record_type):
    limit = 0 if not size else size
    if not size and page > 0:
        limit = _DEFAULT_PAGE_SIZE
    offset = 0 if not page else (page - 1) * limit

    record_list = []
    records, count = credit_db.get_credit_records(
            user_id, limit, offset, record_type)
    for record in records:
        rec = RecordLite()
        rec.title = record.title
        rec.amount = record.amount
        rec.time = utc_to_local(
                record.created_at).strftime('%Y-%m-%d %H:%M:%S')
        record_list.append(rec)

    return record_list, count


def get_latest_distribution():
    latest_term = credit_db.get_latest_distribution_term()
    if not latest_term:
        return None, None, []
    records = credit_db.get_latest_distribution(latest_term.id) 
    d_list = []
    for record in records:
        user_info = {} if not record.user_info else json.loads(record.user_info)
        d_list.append({
            'user_id': record.user_id,
            'nick_name': user_info.get('nick_name'),
            'avatar_id': user_info.get('avatar_id'),
            'amount': record.amount,
        })
    return latest_term.date, latest_term.id, d_list
