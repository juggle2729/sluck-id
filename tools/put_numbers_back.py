# -*- coding: utf-8 -*-
import json
import sys

import os
from sqlalchemy import func

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'
from luckycommon.cache import redis_cache
from luckycommon.model.activity import UserActivity, Activity


def put_back(activity_id):
    activity = Activity.query.filter(Activity.id == activity_id).first()
    lucky_numbers = range(1, activity.target_amount + 1)
    redis_cache.generate_numbers(activity.id, *lucky_numbers)
    uas = UserActivity.query.filter(UserActivity.activity_id == activity_id).all()
    uniques = []
    numbers = []
    for ua in uas:
        nums = ua.numbers.split(',')
        numbers += nums

    raw_numbers = [int(x) - 10000001 for x in numbers]
    uniques = list(set(raw_numbers))
    redis_cache.lock_numbers(activity_id, *raw_numbers)
    print len(raw_numbers), len(uniques)


put_back('8157db8d-0473-35f9-8275-1ba0bce8e990')
