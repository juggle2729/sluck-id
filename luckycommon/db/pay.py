# -*- coding: utf-8 -*-
import json
import logging
from decimal import Decimal
from datetime import datetime

from sqlalchemy import func, text

from luckycommon.model import orm, slave
from luckycommon.model.pay import PayStatus, Pay
from luckycommon.account.model.account import Account
from luckycommon.utils import id_generator
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.orm import get_count
from luckycommon.db.helper import (generate_filter, parse_query_dct,
                                   get_orderby, paginate)


_LOGGER = logging.getLogger('lucky')

USER_TYPE = {
    'new_user': 1,
    'next_day_user': 2,
    'week_user': 3,
    'old_user': 4,
}


@sql_wrapper
def get_pay(pay_id):
    return Pay.query.filter(Pay.id == pay_id).first()


@sql_wrapper
def list_pay(query_dct):
    user_type = int(query_dct.pop('user_type', 0))
    query_dct = parse_query_dct(query_dct, Pay)
    query = orm.session.query(Pay, Account.created_at.label('ac_t')).join(
        Account, Account.id == Pay.user_id)
    if user_type:
        diff = func.timestampdiff(
            text('DAY'), Account.created_at, Pay.created_at)
        if user_type == 1:
            query = query.filter(diff == 0)
        elif user_type == 2:
            query = query.filter(diff == 1)
        elif user_type == 3:
            query = query.filter(diff > 1).filter(diff < 7)
        else:
            query = query.filter(diff >= 7)
    query = query.filter(generate_filter(query_dct, Pay))
    total_count = get_count(query)
    if '$orderby' in query_dct:
        query = query.order_by(get_orderby(query_dct['$orderby'], Pay))
    query = paginate(query, query_dct)

    return query.all(), total_count


@sql_wrapper
def get_pay_overview(parsed_dct):
    query = orm.session.query(Pay.pay_type, func.count(Pay),
                              func.sum(Pay.price))
    query = query.filter(generate_filter(parsed_dct, Pay))
    if 'pay_type' not in parsed_dct:
        query = query.group_by(Pay.pay_type)
    resp = []
    for r in query.all():
        # (type, count , sum)
        resp.append({
            "pay_type": r[0] or parsed_dct.get('pay_type', 0),
            "count": r[1],
            "total": float(r[2]) if r[2] is not None else 0,
        })
    return resp


@sql_wrapper
def create_pay(user_id, pay_type):
    Pay.query.filter(Pay.user_id == user_id)\
             .filter(Pay.pay_type == pay_type)\
             .filter(Pay.status == PayStatus.WAIT.value)\
             .delete()
    pay = Pay()
    pay.id = id_generator.generate_long_id('pay')
    pay.user_id = user_id
    pay.pay_type = pay_type
    pay.status = PayStatus.WAIT.value
    pay.save()
    return pay


@sql_wrapper
def fill_pay(pay_id, pay_amount, activity_id, quantity):
    fill_dict = {
        'activity_id': activity_id,
        'quantity': quantity,
        'updated_at': datetime.utcnow()
    }
    if pay_amount is not None:
        fill_dict.update({'price': Decimal(pay_amount)})
    Pay.query.filter(Pay.id == pay_id).update(fill_dict)
    orm.session.commit()


@sql_wrapper
def update_pay_ext(pay_id, ext):
    pay = Pay.query.filter(Pay.id == pay_id).with_lockmode('update').first()
    extend = {} if not pay.extend else json.loads(pay.extend)
    extend.update(ext)
    pay.extend = json.dumps(extend, ensure_ascii=False)
    pay.save()


@sql_wrapper
def submit_pay_commit(pay_id, user_id):
    res = Pay.query.filter(Pay.id == pay_id)\
                   .filter(Pay.user_id == user_id)\
                   .filter(Pay.status == PayStatus.WAIT.value)\
                   .update({'status': PayStatus.SUBMIT.value})
    orm.session.commit()
    if res:
        return Pay.query.filter(Pay.id == pay_id).one()
    return None


@sql_wrapper
def submit_pay_revert(pay_id):
    Pay.query.filter(Pay.id == pay_id)\
             .filter(Pay.status == PayStatus.SUBMIT.value).update(
        {'status': PayStatus.WAIT.value})
    orm.session.commit()
