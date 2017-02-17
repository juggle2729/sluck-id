# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json

from sqlalchemy import distinct

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.model import orm
from luckycommon.account.model.account import Account
from luckycommon.model.activity import ActivityWin
from luckycommon.utils.template import generate_from_template

from luckycommon.notification.model.notification import *
from luckycommon.notification.db.notification import generate_sys_notification, generate_notification


def generate_extend():
    extend = {
        'filter_list': [
        {
            'chn': {
                'exclude': ['ios']
            },
            'cvc': {
                'max': 12,
                'min': 1
            }
        }],
        'alert': {
            'image': '',
            'cmd': '11#http://121.41.6.238:9898/discovery/first_double_charge'
        }
    }
    return json.dumps(extend)


cmd = sys.argv[1]
if cmd == 'update':
    content = generate_from_template('update_notify')
    generate_sys_notification(content, extend=generate_extend())


if cmd == 'test' and sys.argv[2]:
    uid = sys.argv[2]
    content = generate_from_template('update_notify')
    generate_notification(uid, content, NOTIFY_TYPE.SYSTEM,
                          extend=generate_extend())
    print 'test push notification to uid: %s' % uid
