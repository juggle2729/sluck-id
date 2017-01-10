# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.activity import ActivityWin

from luckycommon.cache import redis_cache


activity_win_list = ActivityWin.query.all()

for aw in activity_win_list:
    user_id = aw.winner
    activity_id = aw.activity_id
    redis_cache.add_user_winn(user_id, activity_id)
    print 'add %s:%s' % (user_id, activity_id)
