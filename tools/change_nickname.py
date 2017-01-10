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

from luckycommon.cache import redis_cache
from luckycommon.db import account as account_db


cmd = sys.argv[1]
if cmd == 'start':
    fp = open('./agent_list', 'r')
    for line in fp:
        uid, nick_name = line.strip().split('\t')
        account_db.update_account({'id': uid, 'nick_name': nick_name})
        print 'changed user %s' % uid
