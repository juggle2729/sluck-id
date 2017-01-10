# -*- coding: utf-8 -*-
import sys
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "luckyplatform.settings")

from luckycommon.order.model.order import AwardedOrder
from luckycommon.db.activity import get_activity
from luckycommon.db.goods import get_goods

with open('/tmp/tax.txt') as f:
    ship_orders = f.readlines()
    for ship_order in ship_orders:
        ship_order = ship_order.strip()
        x = AwardedOrder.query.filter(
            AwardedOrder.extend.like('%%%s%%' % ship_order)).first()
        if not x:
            print u'noooo'
            continue

        activity = get_activity(x.activity_id)
        goods = get_goods(activity.goods_id)
        if goods.source_type == 1:
            print u'jdzy'
        else:
            print u'fjdzy'
