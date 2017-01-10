# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
from datetime import timedelta
from sqlalchemy import func

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.stats import MG as mg
from luckycommon.model.coupon import COUPON_STATUS, AccountCoupon
from luckycommon.model import orm
from luckycommon.model.missed_vips import MissedVips, BackVips
from luckycommon.db.missed_vips import batch_insert_back_vips
from luckycommon.utils import tz


today = tz.local_now()
today_str = today.strftime('%Y-%m-%d')
to_insert = []


# N天前
for k in (3, 7, 14):
    call_at = (today - timedelta(days=k)).strftime('%Y-%m-%d')
    call_at_utc = tz.get_utc_date(call_at)
    # 流失天数
    for l in (3, 7, 14, 30):
        # 用户类型
        for u in (0, 1):
            if u == 1 and l > 3:
                continue
            items = orm.session.query(MissedVips.uid).filter(
                MissedVips.created_at == call_at).filter(
                MissedVips.lost_days == l).filter(
                MissedVips.user_type == u).all()
            uids = set()
            for item in items:
                uids.add(item[0])
            if len(uids) == 0:
                continue
            uids = list(uids)
            data = {
                'calc_at': today_str,
                'lost_days': l,
                'call_at': call_at,
                'total_count': len(uids),
                'back_count': 0,
                'recharge_count': 0,
                'recharge_amount': 0,
                'win_count': 0,
                'win_amount': 0,
                'coupon_amount': 0,
                'pay_count': 0,
                'user_type': u
            }
            for uid in uids:
                t = mg.user_stats.find_one({"_id": uid})
                if not t:
                    continue
                elif t.get('updated_at') and t['updated_at'] > call_at_utc:
                    data['back_count'] += 1
                t = mg.daily_stats.aggregate([
                    {'$match': {'$and': [
                        {'updated_at': {'$gte': call_at_utc}},
                        {'user_id': uid}
                    ]}},
                    {'$group': {'_id': None,
                                'recharge': {'$sum': '$recharge.total'},
                                'win': {'$sum': '$win.total'},
                                'pay': {'$sum': 1}}}
                ])
                t = t.next() if t.alive else {}
                recharge = t.get('recharge', 0)
                if recharge > 0:
                    data['recharge_count'] += 1
                    data['recharge_amount'] += recharge
                win = t.get('win', 0)
                if win > 0:
                    data['win_count'] += 1
                    data['win_amount'] += win
                pay = t.get('pay', 0)
                if pay > 0:
                    data['pay_count'] += 1

                coupon_amount = orm.session.query(
                    func.sum(AccountCoupon.price)).filter(
                    AccountCoupon.created_at >= call_at_utc).filter(
                    AccountCoupon.user_id == uid).filter(
                    AccountCoupon.status == COUPON_STATUS.USED).scalar()
                if coupon_amount:
                    data['coupon_amount'] += int(float(coupon_amount))
            to_insert.append(data)

batch_insert_back_vips(to_insert)
