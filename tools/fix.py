# -*- coding: utf-8 -*-
from __future__ import absolute_import


import sys
import os
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.account.model.account import Account

def fix():
    accs = Account.query.filter(Account.is_virtual==1).all()
    for acc in accs:
        redis_cache.add_virtual_account(acc.id)
    

if __name__ == "__main__":
    print 'Start fix job at: {0}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    fix()
    print 'End fix job at: {0}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

