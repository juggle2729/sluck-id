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

from luckycommon.model import orm
from luckycommon.model.activity import ActivityTemplate

cmd = sys.argv[1]
if cmd == 'update':
    fp = open('./short_title', 'r')
    for line in fp:
        line = line.strip()
        tid, short_title = line.split('\t')
        print tid, short_title
        ActivityTemplate.query.filter(ActivityTemplate.id == tid).update({
            'short_title': short_title
        })
    orm.session.commit()
