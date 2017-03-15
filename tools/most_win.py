# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache  import redis_cache
from luckycommon.model.activity import Activity, ActivityWin

from django.conf import settings

virtual_set = redis_cache.get_virtual_account()

user_dict = {}
a_dict = {}
print 'start...'
print settings.DEBUG
activity_wins = ActivityWin.query.all()
print 'fetch %s items' % len(activity_wins)
for ua in activity_wins:
    activity_id = ua.activity_id
    user_id = ua.winner
    if str(user_id) in virtual_set: 
        continue
    activity = Activity.query.filter(Activity.id == activity_id).first()
    template_id = activity.template_id
    name = activity.name
    key = '%s-%s' % (template_id, name)
    a_dict.setdefault(key, {'uids': set(), 'count': 0, 'amount': activity.target_amount})
    a_dict[key]['uids'].add(user_id)
    a_dict[key]['count'] += 1
    print 'add %s to %s' % (user_id, template_id)

b_dict = [{'id':k,'user_count':len(v['uids']),'count': v['count'],'amount':v['amount']} for k,v in a_dict.items()]
b_dict.sort(key=lambda x: x['user_count'], reverse=True)
for item in b_dict:
    print '%s\t%s\t%s\t%s' % (item['id'], item['user_count'], item['count'], item['amount'])
