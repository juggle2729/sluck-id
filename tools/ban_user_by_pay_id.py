# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.account.db.account import get_account
from luckycommon.db.pay import get_pay

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'input pay_id list with comma separated'
    pay_id_list = sys.argv[1].split(',')
    need_ban = False
    if len(sys.argv) == 3:
        option = sys.argv[2]
        if 'ban' == option:
            need_ban = True
    for pay_id in pay_id_list:
        pay = get_pay(pay_id)
        if not pay:
            print 'pay_id: %s not found' % pay_id
            continue
        print 'pay_id: %s, user_id: %s' % (pay_id, pay.user_id)
        if need_ban:
            account = get_account(pay.user_id)
            if not account:
                continue
            account.status = 1
            account.save()
            print 'ban %s' % account.id
