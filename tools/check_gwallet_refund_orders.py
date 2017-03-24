# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys
import json
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.account.db.account import get_account, black_account
from luckycommon.model.pay import PayStatus, Pay


def check_gwallet_refund_orders(orders):
    order_user_mappings = {}
    res = Pay.query.filter(Pay.pay_type == 20).filter(Pay.status == PayStatus.DONE.value).all()
    for item in res:
        if item.extend:
            trade_no = json.loads(item.extend)['trade_no']
            order_user_mappings[trade_no] = [int(item.user_id), item.updated_at]

    banned_users = []
    for oid in orders:
        if oid not in order_user_mappings:
            print '{0} is not in database.'.format(oid)
            continue
        user_id, updated_time = order_user_mappings[oid]
        account = get_account(user_id)
        if account.status == 0:
            print '{0} is not banned, order id is {1}'.format(user_id, oid)
            block_reason = 'block account by gwallet refund, order id is {0}, voided time is {1}, ' \
                           'block time is {2}'.format(oid, updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                                                      datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            black_account(user_id, block_reason)
        else:
            banned_users.append(user_id)
    # print all banned user ids
    print list(set(banned_users))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'no orders'
    else:
        check_gwallet_refund_orders(sys.argv[1].split(','))