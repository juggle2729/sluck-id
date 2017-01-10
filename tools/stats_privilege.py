# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.strategy import StrategyPrivilege, PRIVILEGE_TYPE


cmd = sys.argv[1]
if cmd == 'check':
    now = datetime.datetime.now() 
    start_date = now - datetime.timedelta(days=1)
    start_date = start_date.replace(hour=16, minute=0, second=0, microsecond=0)
    items = StrategyPrivilege.query.filter(StrategyPrivilege.updated_at > start_date.strftime('%Y-%m-%d %H:%M:%S')).all()
    created_dict = {}
    used_dict = {}
    for item in items:
        privilege_type = item.privilege_type
        if item.created_at > start_date:
            created_dict.setdefault(privilege_type, 0)
            created_dict[privilege_type] += 1
        if item.used:
            used_dict.setdefault(privilege_type, 0)
            used_dict[privilege_type] += 1
    html = '<html><body>'
    html += u'<h1>今日产生特权</h1><br />'
    for k,v in created_dict.items():
        html += u'特权类型:%s\t数量:%s <br />' % (PRIVILEGE_TYPE.get_label(k), v)
    html += u'<h1>今日使用特权</h1><br />'
    for k,v in used_dict.items():
        html += u'特权类型:%s\t数量:%s' % (PRIVILEGE_TYPE.get_label(k), v)
    html += '</body></html>'
    print html
