# -*- coding: utf-8 -*-
from __future__ import absolute_import

import time
from datetime import datetime
import sys
import os

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'


from luckycommon.account.model.account import Account
from luckycommon.model.pay import Pay

def _get_all_banned_user_id():
    banned_users = Account.query.filter(Account.status == 1).all()
    list_user = []
    for user in banned_users:
        list_user.append(user.id)
    return list_user


def _get_user_total_amount(userid_list):
    for user_id in userid_list:
        Pays = Pay.query.filter(Pay.user_id == user_id).filter(Pay.status == 2).all()
        amount = 0
        for pay in Pays:
            if pay.price:
                amount += pay.price
        print 'user id: ', user_id, ' total amount: ', amount

if __name__ == '__main__':
    users = _get_all_banned_user_id()
    _get_user_total_amount(users)