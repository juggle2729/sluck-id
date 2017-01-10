# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import random
from luckycommon.db.coupon import set_coupon_scope
from luckycommon.cache import redis_cache


conf_list = [
    {
        'c_tid': 139,
        'a_tids': [416,417,221,419,418,420,
                   400,303,401,402,403,404,
                   405,406,407,410,409,408,
                   249,411,412,413,414,415]
    },
    {
        'c_tid': 140,
        'a_tids': [416,417,221,419,418,420,
                   400,303,401,402,403,404,
                   405,406,407,410,409,408,
                   249,411,412,413,414,415]
    },
    {
        'c_tid': 141,
        'a_tids': [416,417,221,419,418,420,
                   400,303,401,402,403,404,
                   405,406,407,410,409,408,
                   249,411,412,413,414,415]
    },
    {
        'c_tid': 142,
        'a_tids': [416,417,221,419,418,420,
                   400,303,401,402,403,404,
                   405,406,407,410,409,408,
                   249,411,412,413,417,415]
    },
]



if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        for conf in conf_list:
            c_tid = conf['c_tid'] 
            a_tids = conf['a_tids']
            for a_tid in a_tids:
                try:
                    set_coupon_scope(c_tid, a_tid)
                except Exception as e:
                    print 'set exception, %s' % e
