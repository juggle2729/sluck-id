# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.pay import Pay
from luckycommon.account.model.account import Account
from luckycommon.model.coupon import AccountCoupon


coupons = AccountCoupon.query.filter(AccountCoupon.coupon_type==2).all()
user_set = set()
used_set = set()
count = 0
for coupon in coupons:
    user_id = coupon.user_id
    status = coupon.status
    account = Account.query.filter(Account.id == user_id).one()
    register_time = account.created_at
    coupon_time = coupon.created_at
    interval = coupon_time - register_time
    i_seconds = interval.seconds
    if i_seconds < 5:
        print user_id, coupon.id, i_seconds
        count += 1
        user_set.add(user_id)
        if status == 2:
            used_set.add(user_id)

print 'found %d account register from coupon, %d used the coupon' % (len(user_set), len(used_set))

pay_set = set()
items = Pay.query.filter(Pay.user_id.in_(list(user_set))).filter(Pay.status==2).all()
sum_price = 0
for item in items:
    sum_price += item.price
    pay_set.add(item.user_id)

print 'sum pay:%s' % sum_price
print 'pay count:%s' % len(pay_set)
