# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import tablib
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckyapi.logic.crowdfunding import create_activity_lite

from luckycommon.cache import redis_cache
from luckycommon.db.activity import get_activitys_by_ids


cmd = sys.argv[1]
if cmd == 'check':
    id_list = redis_cache.get_latest_announce(start=0, num=10)
    activitys = get_activitys_by_ids(id_list)
    lite_list = []
    for activity in activitys:
        lite_obj = create_activity_lite(activity)
        lite_list.append(lite_obj)
