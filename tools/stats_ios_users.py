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

for account in Account.query.filter(Account.extend == '{"logon": true, "pkg": "none", "chn": "qg_ios"}').all():
    user_id = account.id
    query_result = orm.session.query(func.sum(Transaction.price)).filter(Transaction.user_id == user_id).filter(
        Transaction.type == TRANSACTION_TYPE.IN).filter(Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if query_result:
        total_recharge = float(query_result)
    else:
        total_recharge = 0
    print '%s, %s' % (user_id, total_recharge)
