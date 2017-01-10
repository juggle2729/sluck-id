# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.model.activity import ActivityWin
from luckycommon.db.activity import get_activity


winner_dict = {}

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        items = ActivityWin.query.filter(ActivityWin.created_at>'2016-01-05 16:00:00').all()
        for item in items:
            user_id = item.winner
            activity_id = item.activity_id
            #activity = get_activity(activity_id)
            if not redis_cache.is_virtual_account(user_id):
                winner_dict.setdefault(user_id, [])
                winn_list = winner_dict[user_id]
                winn_list.append(activity_id)

        l = [{'uid': k, 'count': len(v), 'a_list': v} for k,v in winner_dict.items()]
        l.sort(key=lambda x: x.get('count'), reverse=True)
        for i in l:
            a_list = i['a_list']
            total_price = 0
            for a in a_list:
                activity = get_activity(a)
                total_price += activity.target_amount
            print '%s  %s' % (i, total_price)
