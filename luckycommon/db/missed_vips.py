# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from luckycommon.model import orm
from luckycommon.model.coupon import AccountCoupon, COUPON_STATUS
from luckycommon.utils.orm import get_count
from luckycommon.model.missed_vips import (MissedVips, CALLBACK_STATUS,
                                           BackVips)
from luckycommon.utils.tz import local_now, get_utc_date
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import (get_orderby, parse_query_dct,
                                   generate_filter, list_object)
from luckycommon.stats import MG as mg

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def batch_insert_missed_vips(data, created_at=None):
    if not data:
        return
    if created_at is None:
        created_at = local_now().strftime('%Y-%m-%d')
    engine = orm.get_engine(None, None, None)
    for i, d in enumerate(data):
        d['status'] = CALLBACK_STATUS.UNCALLED
        d['created_at'] = created_at
        d['updated_at'] = datetime.utcnow()
        d['rank'] = i + 1
    engine.execute(MissedVips.__table__.insert(), data)


@sql_wrapper
def batch_insert_back_vips(data):
    if not data:
        return
    engine = orm.get_engine(None, None, None)
    engine.execute(BackVips.__table__.insert(), data)


@sql_wrapper
def batch_update_missed_vips(ids, status):
    for id in ids:
        vip = MissedVips.query.with_for_update().filter(
            MissedVips.id == id).first()
        if vip:
            vip.status = vip.status | status if status != 0 else 0
            vip.save()


@sql_wrapper
def list_back_vips(query_dct):
    return list_object(query_dct, BackVips)


@sql_wrapper
def list_missed_vips(query_dct):
    status = query_dct.pop('status', None)
    coupon_level = query_dct.pop('coupon_level', None)
    query_dct = parse_query_dct(query_dct, MissedVips)
    query = MissedVips.query
    if status is not None:
        status = int(status)
        if status == 0:
            query = query.filter(MissedVips.status == 0)
        else:
            query = query.filter(MissedVips.status.op('&')(status) > 0)
    if coupon_level is not None:
        coupon_level = int(coupon_level)
        if coupon_level == 1:
            query = query.filter(MissedVips.recharge_amount < 1000)
        elif coupon_level == 2:
            query = query.filter(MissedVips.recharge_amount >= 1000).filter(
                MissedVips.recharge_amount < 4000)
        elif coupon_level == 3:
            query = query.filter(MissedVips.recharge_amount >= 4000)
    query = query.filter(generate_filter(query_dct, MissedVips))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), MissedVips)
    if orderby is not None:
        query = query.order_by(orderby)

    return query.all(), total_count


@sql_wrapper
def calc_back_info(day):
    resp = {
        3: {"stay_rate": 0, "recharge_rate": 0, "back_rate": 0},
        7: {"stay_rate": 0, "recharge_rate": 0, "back_rate": 0},
        14: {"stay_rate": 0, "recharge_rate": 0, "back_rate": 0}
    }
    back_info = {}
    today = get_utc_date()
    yesterday = today - timedelta(days=1)
    if day is None:
        day = yesterday.strftime('%Y-%m-%d')
    for d in resp.keys():
        items = orm.session.query(MissedVips.uid).filter(
            MissedVips.created_at == day).filter(
            MissedVips.lost_days == d).all()
        uids = [k[0] for k in items]
        if not uids:
            continue
        # 回流率
        # 付费率
        users = mg.user_stats.find({"_id": {"$in": uids},
                                    "updated_at": {"$gte": get_utc_date(day)}})
        back_count = recharge_count = 0
        for user in users:
            uid = user['_id']
            back_count += 1
            back_info[uid] = {
                "recharge": 0,
                "used_coupon": 0,
                "updated_at": user['updated_at']
            }
            x = mg.daily_stats.aggregate([
                {"$match": {"$and": [
                    {"user_id": uid},
                    {"updated_at": {"$gte": get_utc_date(day)}}
                ]}},
                {"$group": {"_id": None,
                            "recharge": {"$sum": "$recharge.total"}}}
            ])
            x = x.next() if x.alive else {}
            if x.get('recharge', 0) > 0:
                back_info[uid]["recharge"] = x.get('recharge')
                recharge_count += 1
            back_info[uid]['used_coupon'] = orm.session.query(
                func.count(AccountCoupon)).filter(
                AccountCoupon.status == COUPON_STATUS.USED).filter(
                AccountCoupon.user_id == uid).filter(
                AccountCoupon.title.like(u'%心跳%')).scalar()

        # 留存率
        if back_count > 0:
            resp[d]['back_rate'] = back_count * 1.0 / len(uids)
            resp[d]['recharge_rate'] = recharge_count * 1.0 / back_count
            t = mg.user_stats.aggregate([
                {"$match": {"$and": [
                    {"_id": {"$in": uids}},
                    {"updated_at": {"$gte": today}}
                ]}},
                {"$group": {"_id": None, "count": {"$sum": 1}}}
            ])
            t = t.next() if t.alive else {}
            resp[d]['stay_rate'] = t.get('count', 0) * 1.0 / back_count

    return resp, back_info
