# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.utils.tz import now_ts
from luckycommon.cache import redis_cache


_SCROLLING_LIMIT = 20


cmd = sys.argv[1]
if cmd == 'scrolling':
    ts = now_ts()
    scrolling_dict = {
        'text': u'请升级到最新版本，有惊喜哦！',
        'cmd': '8#'
    }
    redis_cache.submit_scrolling(json.dumps(scrolling_dict, ensure_ascii=False), ts)
    # check to Trim
    if redis_cache.get_scrolling_count() > _SCROLLING_LIMIT:
        redis_cache.trim_scrolling()
