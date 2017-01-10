# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import random
from luckycommon.model.coupon import AccountCoupon, CouponTemplate
from luckycommon.cache import redis_cache



if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        fp = open('./coupon_template', 'r')
        for line in fp:
            id, title, desc, coupon_type, price, condition_price, valid_ts = line.split('\t')
            template = CouponTemplate()
            template.id = id
            template.coupon_type = coupon_type
            template.title = title
            template.desc = desc
            template.price = price
            if coupon_type == '2':
                template.condition_price = int(condition_price)
            template.valid_ts = int(valid_ts) * 24 * 3600
            template.save()
    if cmd == 'random':
        user_id = int(sys.argv[2])
        num = int(sys.argv[3])
        for _ in range(num):
            tid = random.randint(1,30)
            template = CouponTemplate.query.filter(CouponTemplate.id == tid).first()
            coupon = AccountCoupon.create_from_template(template, user_id)
            coupon.save()
            AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
    if cmd == 'one':
        user_id = int(sys.argv[2])
        tid = int(sys.argv[3])
        template = CouponTemplate.query.filter(CouponTemplate.id == tid).first()
        coupon = AccountCoupon.create_from_template(template, user_id)
        coupon.save()
        AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
