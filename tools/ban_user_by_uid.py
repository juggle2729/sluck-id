# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.account.db.account import get_account

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'input user_id list with comma separated'
    user_id_list = sys.argv[1].split(',')
    for user_id in user_id_list:
        account = get_account(user_id)
        if not account:
            continue
        account.status = 1
        account.save()
        print 'ban %s' % account.id
