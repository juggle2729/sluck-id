# -*- coding: utf-8 -*-
"""
检查虚拟商品的红包使用情况
"""
from __future__ import absolute_import
import os
import sys
import json
import tablib
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.db.activity import get_activity
from django.conf import settings

fd = open('/home/ubuntu/af-env/data/t.json', 'r')
for line in fd:
    o = json.loads(line.strip())
    target = o['target']
    ts = o['@timestamp']
    bingo = False
    if isinstance(target, list):
        for t in target:
            aid = t['activity_id']
            activity = get_activity(aid)
            if activity.template_id in settings.CARD_TIDS:
                bingo = True
                break
    else:
        activity = get_activity(target)
        if activity.template_id in settings.CARD_TIDS:
            bingo = True
    if bingo:
        print line.strip()
