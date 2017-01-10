# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime

from pymongo import MongoClient

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "luckyplatform.settings")

from luckycommon.utils.tz import get_utc_date
from redis import StrictRedis

mg = MongoClient('127.0.0.1').lucky
rd = StrictRedis("127.0.0.1", 6379)

from_date = "2016-01-27"


def daily_traverse():
    start_time = get_utc_date(from_date)
    items = mg.daily_stats.find({
        "updated_at": {"$gt": start_time}
    })
    for item in items:
        key = "stats:user:%s" % item["user_id"]
        if "created_at" in item:
            mg.user_stats.remove({"_id": item["user_id"]})
            rd.delete(key)
        else:
            update_dct = {"$inc": {}}
            for t in "recharge", "win", "pay":
                if t in item:
                    rd.hincrby(key, "total_%s" % t, 0 - int(item[t]["total"]))
                    if t == "win":
                        rd.hincrby(key, "win_count", 0 - int(
                            item["win"].get("count", 0)))
                    for k, v in item[t].iteritems():
                        if not k.endswith('_at'):
                            update_dct["$inc"]["%s.%s" % (t, k)] = 0 - v
            if update_dct["$inc"]:
                mg.user_stats.update({"_id": item["user_id"]}, update_dct)

        mg.daily_stats.remove({"_id": item["_id"]})


if __name__ == '__main__':
    daily_traverse()
