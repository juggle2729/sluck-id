# -*- coding: utf-8 -*-
import sys
import os
import json
from datetime import datetime

from pymongo import MongoClient
from sqlalchemy import func, distinct

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "luckyplatform.settings")

from luckycommon.order.model.order import AwardedOrder

items = AwardedOrder.query.with_for_update().filter(
    AwardedOrder.status == 5).all()

for item in items:
    extend = json.loads(item.extend or '{}')
    by_juhe = extend.get('by_juhe')
    if by_juhe is not None:
        if by_juhe == 2:
            item.ship_status = 2
        elif by_juhe == 0:
            item.ship_status == 1
        extend.pop('by_juhe')
        item.extend = json.dumps(extend, ensure_ascii=False)
        item.save()
