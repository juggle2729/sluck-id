# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import tablib
from datetime import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache

from luckycommon.model import orm
from luckycommon.model.activity import *

from luckycommon.utils import id_generator


cmd = sys.argv[1]
if cmd == 'check':
    items = HotActivity.query.all()
    for item in items:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (item.template_id, item.term_number))
        UserActivity.query.filter(UserActivity.activity_id == activity_id).update({
            'status': ACTIVITY_STATUS.STARTED,
            'updated_at': datetime.utcnow()
        })
    orm.session.commit()
