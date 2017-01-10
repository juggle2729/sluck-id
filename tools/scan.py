from __future__ import absolute_import
import os
import sys
import redis

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.db.activity import get_activity

client = redis.StrictRedis(host='10.46.71.31', port=6379)

cursor = 0
delete_count = 0
while True:
    d = client.scan(cursor, 'lucky:luckyorders:*')
    cursor = int(d[0])
    target_list = d[1]
    print cursor, target_list
    for t in target_list:
        c = t.split(':')
        a_id = c[2]
        activity = get_activity(a_id)
        if activity.status == 4:
            client.delete(t)
            delete_count += 1
    print 'processed %d data' % len(target_list)
    if cursor == 0:
        print 'done'
        break

print 'delete %s' % delete_count
