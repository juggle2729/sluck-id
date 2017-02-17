# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys

import os
from sqlalchemy import func

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model import orm
from luckycommon.account.model.account import Account
from luckycommon.model.transaction import Transaction, TRANSACTION_TYPE, TRANSACTION_STATUS
from luckycommon.order.model.order import AwardedOrder
from luckycommon.model.activity import Activity

paid_user_query_result = orm.session.query(Transaction.user_id).filter(Transaction.type == TRANSACTION_TYPE.IN).filter(
    Transaction.status == TRANSACTION_STATUS.DONE).distinct().all()

result_list = []

for items in paid_user_query_result:
    result_dict = {
        'user_id': None,
        'register_at': None,
        'first_recharge_at': None,
        'first_recharge_amount': 0,
        'last_recharge_at': None,
        'total_recharge_amount': 0,
        'total_award_amount': 0
    }
    user_id = int(items[0])
    account = Account.query.filter(Account.id == user_id).first()
    result_dict['user_id'] = user_id
    result_dict['register_at'] = account.created_at.strftime('%Y-%m-%d')
    first_recharge = Transaction.query.filter(Transaction.user_id == user_id).filter(Transaction.type == TRANSACTION_TYPE.IN).filter(
        Transaction.status == TRANSACTION_STATUS.DONE).first()
    last_recharge = Transaction.query.filter(Transaction.user_id == user_id).filter(Transaction.type == TRANSACTION_TYPE.IN).filter(
        Transaction.status == TRANSACTION_STATUS.DONE).order_by(Transaction.id.desc()).first()
    result_dict['first_recharge_at'] = first_recharge.created_at.strftime('%Y-%m-%d')
    result_dict['first_recharge_amount'] = first_recharge.price
    result_dict['last_recharge_at'] = last_recharge.created_at.strftime('%Y-%m-%d')
    result_dict['total_recharge_amount'] = float(
        orm.session.query(func.sum(Transaction.price)).filter(Transaction.user_id == user_id).filter(
            Transaction.type == TRANSACTION_TYPE.IN).filter(Transaction.status == TRANSACTION_STATUS.DONE).first()[0])
    for award_item in AwardedOrder.query.filter(AwardedOrder.user_id == user_id).all():
        activity = Activity.query.filter(Activity.id == award_item.activity_id).first()
        if activity:
            result_dict['total_award_amount'] += activity.target_amount

    result_list.append(result_dict)

for item in result_list:
    print('%s,%s,%s,%s,%s,%s,%s' % (
        item['user_id'], item['register_at'], item['first_recharge_at'], item['first_recharge_amount'], item['last_recharge_at'], item[
            'total_recharge_amount'], item['total_award_amount']))
