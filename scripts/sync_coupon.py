# -*- coding: utf-8 -*-
import sys
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "luckyplatform.settings")

from luckycommon.stats import MG as mg
from luckycommon.model.coupon import AccountCoupon

items = mg.coupon.find({'status': 1})
for item in items:
    cp = AccountCoupon.query.filter(AccountCoupon.id == item['_id']).first()
    if not cp:
        print "can't find ", item["_id"]
        continue
    if cp.status != 1:
        mg.coupon.update_one({'_id': item['_id']}, {
                             '$set': {'status': cp.status}})
