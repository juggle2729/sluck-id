# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

from sqlalchemy import func

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model import orm
from luckycommon.account.model.account import Account
from luckycommon.model.transaction import Transaction, TRANSACTION_TYPE, TRANSACTION_STATUS

users_with_phone_in_month = Account.query.filter(Account.phone != None).filter(Account.created_at > '2017-03-01').filter(
    Account.created_at < '2017-04-01').filter(Account.is_virtual == 0).all()

for user in users_with_phone_in_month:
    user_id = user.id
    result = orm.session.query(func.sum(Transaction.price)).filter(Transaction.user_id == user_id).filter(
        Transaction.type == TRANSACTION_TYPE.IN).filter(Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if result:
        total_recharge = float(result)
    else:
        total_recharge = 0
    try:
        print '%s, %s, %s, %s, %s' % (user.created_at, user.nick_name.encode('utf-8'), user.id, user.phone, total_recharge)
    except UnicodeDecodeError:
        print '%s, %s, %s, %s, %s' % (user.created_at, None, user.id, user.phone, total_recharge)
