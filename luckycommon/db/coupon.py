# -*- coding: utf-8 -*-
import json
import random
import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from luckycommon.model import orm
from luckycommon.account.model.account import Account
from luckycommon.model.coupon import *
from luckycommon.model.transaction import *
from luckycommon.utils.tz import (now_ts, get_utc_date, utc_to_local,
                                  local_to_utc)
from luckycommon.utils import id_generator
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.exceptions import (ResourceInsufficient,
                                          AuthenticateError, ServerError)
from luckycommon.db.helper import list_object

_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@sql_wrapper
def get_coupon(coupon_id, user_id, need_valid=True):
    query = AccountCoupon.query.filter(AccountCoupon.id == coupon_id)\
                               .filter(AccountCoupon.user_id == user_id)
    if need_valid:
        now = now_ts()
        query = query.filter(AccountCoupon.status == COUPON_STATUS.UNUSED)\
                     .filter(AccountCoupon.start_ts < now)\
                     .filter(AccountCoupon.expire_ts > now)
    return query.first()


@sql_wrapper
def get_user_coupons(user_id, status, limit=0, offset=0):
    query = AccountCoupon.query
    count_query = orm.session.query(orm.func.count(AccountCoupon.id))
    query = query.filter(AccountCoupon.user_id == user_id)
    count_query = count_query.filter(AccountCoupon.user_id == user_id)
    if status is not None:
        junction = orm.or_
        status_filters = []
        if status & COUPON_STATUS.UNUSED:
            status_filters.append(AccountCoupon.status == COUPON_STATUS.UNUSED)
        if status & COUPON_STATUS.USED:
            status_filters.append(AccountCoupon.status == COUPON_STATUS.USED)
        if status & COUPON_STATUS.EXPIRED:
            status_filters.append(
                AccountCoupon.status == COUPON_STATUS.EXPIRED)
        query = query.filter(junction(*status_filters))
        count_query = count_query.filter(junction(*status_filters))
    count = count_query.all()[0][0]
    query = query.order_by(AccountCoupon.created_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    coupons = query.all()
    return coupons, count


@sql_wrapper
def list_coupon(query_dct):
    return list_object(query_dct, AccountCoupon)


@sql_wrapper
def get_unused_coupons(user_id, limit=0, offset=0):
    query = AccountCoupon.query
    query = query.filter(AccountCoupon.user_id == user_id)\
                 .filter(AccountCoupon.status == COUPON_STATUS.UNUSED)
    query = query.order_by(AccountCoupon.start_ts).order_by(
        AccountCoupon.price.desc()).order_by(AccountCoupon.expire_ts)
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    coupons = query.all()
    return coupons


@sql_wrapper
def get_coupon_scope(coupon_tid):
    return CouponScope.query.filter(CouponScope.coupon_tid == coupon_tid).all()


@sql_wrapper
def set_coupon_scope(coupon_tid, activity_tid):
    coupon_scope = CouponScope()
    coupon_scope.coupon_tid = coupon_tid
    coupon_scope.activity_tid = activity_tid
    coupon_scope.save()


@sql_wrapper
def get_group_coupon(group_coupon_id, need_valid=True):
    query = GroupCoupon.query.filter(GroupCoupon.id == group_coupon_id)
    if need_valid:
        now = now_ts()
        query = query.filter(GroupCoupon.expire_ts > now)
    return query.first()


@sql_wrapper
def get_coupon_by_id(coupon_id):
    return AccountCoupon.query.filter(AccountCoupon.id == coupon_id).first()


@sql_wrapper
def expire_coupon(coupon_id):
    coupon = AccountCoupon.query.filter(AccountCoupon.id == coupon_id).one()
    if coupon.status == COUPON_STATUS.UNUSED:
        coupon.status = COUPON_STATUS.EXPIRED
        coupon.save()
        _TRACKER.info({'user_id': coupon.user_id,
                       'coupon_id': coupon.id,
                       'type': 'expire_coupon',
                       'price': coupon.price})


@sql_wrapper
def use_coupon(coupon):
    res = AccountCoupon.query.filter(AccountCoupon.id == coupon.id).filter(
        AccountCoupon.status == COUPON_STATUS.UNUSED).update({
            'status': COUPON_STATUS.USED,
            'updated_at': datetime.utcnow()
        })
    if res:
        # add balance
        account = Account.query.filter(
            Account.id == coupon.user_id).with_lockmode('update').first()
        account.balance += coupon.price
        account.save(auto_commit=False)
        # add transaction
        transaction = Transaction()
        transaction.id = id_generator.generate_long_id('transaction')
        transaction.user_id = account.id
        transaction.type = TRANSACTION_TYPE.AWARD
        transaction.title = coupon.title
        transaction.price = coupon.price
        transaction.balance = account.balance
        transaction.status = TRANSACTION_STATUS.DONE
        transaction.save(auto_commit=False)
        orm.session.commit()
        return True
    else:
        _LOGGER.warn(
            'use coupon fail, cocurrency occured!, coupon id[%s]' % coupon.id)
        return False


SNATCH_COUPON_RATION = [
    {'start': 1, 'end': 20, 'tid': 87},
    {'start': 20, 'end': 55, 'tid': 88},
    {'start': 55, 'end': 70, 'tid': 89},
    {'start': 70, 'end': 90, 'tid': 90},
    {'start': 90, 'end': 100, 'tid': 91},
]


@sql_wrapper
def snatch_group_coupon(group_coupon_id, phone_number, account=None):
    group_coupon = GroupCoupon.query.filter(
        GroupCoupon.id == group_coupon_id).with_lockmode('update').one()
    if group_coupon.left_count <= 0:
        raise ResourceInsufficient('insufficient')
    group_coupon.left_count -= 1
    internal_coupons = {} if not group_coupon.coupons else json.loads(
        group_coupon.coupons)
    if phone_number in internal_coupons:
        raise AuthenticateError('no access')
    rand_int = random.randint(1, 100)
    for ratio_item in SNATCH_COUPON_RATION:
        if rand_int >= ratio_item['start'] and rand_int <= ratio_item['end']:
            tid = ratio_item['tid']
            break
    if not tid:
        raise ServerError('tid not found')
    internal_coupons.update({phone_number: tid})
    group_coupon.coupons = json.dumps(internal_coupons, ensure_ascii=False)
    template = CouponTemplate.query.filter(CouponTemplate.id == tid).one()
    if account:
        coupon = AccountCoupon.create_from_template(template, account.id)
        coupon.save(auto_commit=False)
        orm.session.flush()
        AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
        _TRACKER.info({'user_id': coupon.user_id,
                       'coupon_id': coupon.id,
                       'type': 'create_coupon',
                       'from': 'snatch',
                       'price': coupon.price})
    else:
        # anonymous
        awaiting_coupon = AwaitingCoupon()
        awaiting_coupon.template_id = tid
        awaiting_coupon.phone = phone_number
        awaiting_coupon.expire_ts = now_ts() + template.valid_ts
        awaiting_coupon.save(auto_commit=False)
    orm.session.commit()
    return template


@sql_wrapper
def check_awaiting_coupon(user_id, phone):
    now = now_ts()
    items = AwaitingCoupon.query.filter(AwaitingCoupon.phone == phone)\
                                .filter(AwaitingCoupon.expire_ts > now)\
                                .filter(AwaitingCoupon.deleted == 0)\
                                .all()
    for item in items:
        template_id = item.template_id
        template = CouponTemplate.query.filter(
            CouponTemplate.id == template_id).one()
        coupon = AccountCoupon.create_from_template(template, user_id)
        coupon.save(auto_commit=False)
        orm.session.flush()
        AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
        item.deleted = 1
        item.save(auto_commit=False)
        _TRACKER.info({'user_id': coupon.user_id,
                       'coupon_id': coupon.id,
                       'type': 'create_coupon',
                       'from': 'awaiting',
                       'price': coupon.price})
    orm.session.commit()


@sql_wrapper
def get_coupon_overview():
    today = get_utc_date()
    resp = {}
    resp["sent_count"], resp["sent_price"] = orm.session.query(
        func.count(AccountCoupon.id), func.sum(AccountCoupon.price)).filter(
        AccountCoupon.updated_at >= today).first()
    resp["used_count"], resp["used_price"] = orm.session.query(
        func.count(AccountCoupon.id), func.sum(AccountCoupon.price)).filter(
        AccountCoupon.status == COUPON_STATUS.USED).filter(
        AccountCoupon.updated_at >= today).first()
    resp["left_count"], resp["left_price"] = orm.session.query(
        func.count(AccountCoupon.id), func.sum(AccountCoupon.price)).filter(
        AccountCoupon.status == COUPON_STATUS.UNUSED).filter(
        AccountCoupon.expire_ts > now_ts()).first()

    for k in resp:
        if resp[k] is None:
            resp[k] = 0

    return resp


@sql_wrapper
def get_coupon_report(date):
    report = {}
    today = get_utc_date(date)
    yesterday = today - timedelta(days=1)
    t = orm.session.query(func.count(AccountCoupon.id),
                          func.sum(AccountCoupon.price)).filter(
        AccountCoupon.created_at >= yesterday).filter(
        AccountCoupon.created_at < today).first()
    report["last_day_sent_count"], report[
        "last_day_sent_price"] = t if t[0] else (0, 0)
    t = orm.session.query(func.count(AccountCoupon.id),
                          func.sum(AccountCoupon.price)).filter(
        AccountCoupon.status == COUPON_STATUS.USED).filter(
        AccountCoupon.updated_at >= yesterday).filter(
        AccountCoupon.updated_at < today).first()
    report["last_day_used_count"], report[
        "last_day_used_price"] = t if t[0] else (0, 0)
    t = orm.session.query(func.count(AccountCoupon.id),
                          func.count(AccountCoupon.price)).filter(
        AccountCoupon.status == COUPON_STATUS.UNUSED).filter(
        AccountCoupon.created_at < today).first()
    report["unused_count_until_today"], report[
        "unused_price_until_today"] = t if t[0] else (0, 0)

    for k in report:
        if k.endswith('price'):
            report[k] = float(report[k])
        else:
            report[k] = int(float(report[k]))

    return report


@sql_wrapper
def award_coupon(user_id, tid):
    template = CouponTemplate.query.filter(CouponTemplate.id == tid).first()
    coupon = AccountCoupon.create_from_template(template, user_id)
    coupon.save()
    AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
    return coupon


def award_coupon_in_transaction(user_id, tid, start_ts=None, extend=None):
    template = CouponTemplate.query.filter(CouponTemplate.id == tid).first()
    coupon = AccountCoupon.create_from_template(template, user_id, extend=extend, start_ts=start_ts)
    coupon.save(auto_commit=False)
    orm.session.flush()
    AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
    _LOGGER.info("add 1 award coupon: %s, user: %s" % (tid, user_id))
    return coupon


@sql_wrapper
def upsert_coupon_template(query_dct):
    if 'id' in query_dct:
        t = CouponTemplate.query.with_for_update().filter(
            CouponTemplate.id == query_dct.pop('id')).first()
    else:
        t = CouponTemplate()

    for k, v in query_dct.iteritems():
        if hasattr(CouponTemplate, k) and k not in (
                'updated_at', 'created_at'):
            setattr(t, k, v)

    t.save()


@sql_wrapper
def list_coupon_template(query_dct):
    return list_object(query_dct, CouponTemplate)


@sql_wrapper
def get_coupon_template(id):
    return CouponTemplate.query.filter(CouponTemplate.id == id).first()
