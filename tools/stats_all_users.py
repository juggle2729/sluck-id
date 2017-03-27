# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import sys

import os
from sqlalchemy import func

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model import orm
from luckycommon.account.model.account import Account
from luckycommon.model.transaction import Transaction, TRANSACTION_TYPE, TRANSACTION_STATUS
from luckycommon.order.model.order import AwardedOrder
from luckycommon.model.activity import Activity, ActivityWin

real_user_query_result = Account.query.filter(Account.is_virtual == 0).all()
paid_user_query_result = orm.session.query(Transaction.user_id).filter(Transaction.type == TRANSACTION_TYPE.IN).filter(
    Transaction.status == TRANSACTION_STATUS.DONE).distinct().all()

for result_dicts in paid_user_query_result:
    result_dict = {
        'user_id': None,
        'total_recharge_amount': 0,
        'buy_count': 0,
        'total_buy_amount': 0,
        'award_count': 0,
        'total_award_amount': 0,
        'register_at': None,
        'last_recharge_at': None,
        'channel': None
    }
    user_id = int(result_dicts[0])
    account = Account.query.filter(Account.id == user_id).first()
    last_recharge = Transaction.query.filter(Transaction.user_id == account.id).filter(Transaction.type == TRANSACTION_TYPE.IN).filter(
        Transaction.status == TRANSACTION_STATUS.DONE).order_by(Transaction.id.desc()).first()
    total_recharge_amount = orm.session.query(func.sum(Transaction.price)).filter(Transaction.user_id == account.id).filter(
            Transaction.type == TRANSACTION_TYPE.IN).filter(Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if total_recharge_amount:
        result_dict['total_recharge_amount'] = float(total_recharge_amount)
    result_dict['user_id'] = account.id
    result_dict['buy_count'] = len(
        Transaction.query.filter(Transaction.user_id == account.id).filter(Transaction.type == TRANSACTION_TYPE.BALANCE_BUY).filter(
            Transaction.status == TRANSACTION_STATUS.DONE).all())
    total_buy_amount = orm.session.query(func.sum(Transaction.price)).filter(Transaction.user_id == account.id).filter(
            Transaction.type == TRANSACTION_TYPE.BALANCE_BUY).filter(Transaction.status == TRANSACTION_STATUS.DONE).first()[0]
    if total_buy_amount:
        result_dict['total_buy_amount'] = float(total_buy_amount)
    result_dict['award_count'] = len(ActivityWin.query.filter(ActivityWin.winner == account.id).all())
    for award_result_dict in AwardedOrder.query.filter(AwardedOrder.user_id == account.id).all():
        activity = Activity.query.filter(Activity.id == award_result_dict.activity_id).first()
        if activity:
            result_dict['total_award_amount'] += activity.target_amount
    result_dict['register_at'] = account.created_at.strftime('%Y-%m-%d')
    if last_recharge:
        result_dict['last_recharge_at'] = last_recharge.created_at.strftime('%Y-%m-%d')
    else:
        result_dict['last_recharge_at'] = account.created_at.strftime('%Y-%m-%d')
    result_dict['channel'] = json.loads(account.extend).get('chn', '')

    print('%s,%s,%s,%s,%s,%s,%s,%s,%s' % (
        result_dict['user_id'], result_dict['total_recharge_amount'], result_dict['buy_count'], result_dict['total_buy_amount'], result_dict['award_count'], result_dict[
            'total_award_amount'], result_dict['register_at'], result_dict['last_recharge_at'], result_dict['channel']))
