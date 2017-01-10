# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import tablib
import datetime
import logging

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model import orm
from luckycommon.model.coupon import *
from luckycommon.utils.tz import now_ts

from django.conf import settings


_TRACKER = logging.getLogger('tracker')


cmd = sys.argv[1]
if cmd == 'expire':
    coupons = AccountCoupon.query.filter(AccountCoupon.expire_ts <= now_ts()).filter(
        AccountCoupon.status==COUPON_STATUS.UNUSED).all()
    for coupon in coupons:
        coupon.status = COUPON_STATUS.EXPIRED
        coupon.save(auto_commit=False)
        log_data = coupon.as_dict()
        log_data.update({
            'type': 'coupon',
            'action': 'expire',
        })
        _TRACKER.info(log_data)
    orm.session.commit()
