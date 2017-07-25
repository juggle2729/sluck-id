# -*- coding: utf-8 -*-
import datetime
import logging

from sqlalchemy import func

from luckycommon.account.model.account import Account
from luckycommon.credit.model.check import *
from luckycommon.credit.model.credit import *
from luckycommon.db.activity import get_activity
from luckycommon.db.show import get_show_by_id
from luckycommon.model.transaction import *
from luckycommon.utils import id_generator
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.exceptions import AuthenticateError, DataError
from luckycommon.utils.orm import get_count
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils.tz import utc_to_local, utc_to_local_str, local_now

_LOGGER = logging.getLogger('lucky')

_REGISTER_CREDIT_AMOUNT = 100
_INVITATION_CREDIT_AMOUNT = 3000
_SHOW_AWARD_RATIO = 1


@sql_wrapper
def get_credit_records(user_id, limit=0, offset=0, record_type=None):
    query = CreditRecord.query.filter(CreditRecord.user_id == user_id)
    count_query = orm.session.query(orm.func.count(CreditRecord.id))\
                             .filter(CreditRecord.user_id == user_id)

    if record_type is not None:
        junction = orm.or_
        type_filters = []
        if record_type & RECORD_TYPE.IN:
            type_filters.append(CreditRecord.type == RECORD_TYPE.IN)
        if record_type & RECORD_TYPE.EXCHANGE:
            type_filters.append(CreditRecord.type == RECORD_TYPE.EXCHANGE)

        query = query.filter(junction(*type_filters))
        count_query = count_query.filter(junction(*type_filters))

    count = count_query.all()[0][0]

    query = query.order_by(CreditRecord.created_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    return query.all(), count


@sql_wrapper
def get_today_checks(user_id):
    today = utc_to_local(datetime.datetime.utcnow())
    today_str = today.strftime('%Y-%m-%d')
    today_checks = AccountDailyCheck.query.filter(AccountDailyCheck.user_id == user_id)\
                                          .filter(AccountDailyCheck.date == today_str)\
                                          .all()
    return today_checks


@sql_wrapper
def get_sign_user_count(start_date=None):
    if not start_date:
        start_date = local_now().replace(hour=0, minute=0, second=0, microsecond=0)
    query = AccountSign.query.filter(AccountSign.last_sign_at > start_date)
    count = get_count(query)
    return count


@sql_wrapper
def get_sign_users(start_date=None, end_date=None):
    if not start_date:
        start_date = local_now().replace(hour=0, minute=0, second=0, microsecond=0)
    query = AccountSign.query.filter(AccountSign.last_sign_at > start_date)
    if end_date:
        query = query.filter(AccountSign.last_sign_at < end_date)
    return query.all() 


@sql_wrapper
def get_user_sign(user_id):
    account_sign = AccountSign.query.filter(
        AccountSign.user_id == user_id).first()
    return account_sign


@sql_wrapper
def daily_check(user_id, check_type):
    today = datetime.datetime.strptime(
        utc_to_local_str(datetime.datetime.utcnow()), '%Y-%m-%d %H:%M:%S')
    today_str = today.strftime('%Y-%m-%d')
    daily_check = AccountDailyCheck.query.filter(AccountDailyCheck.user_id == user_id)\
                                         .filter(AccountDailyCheck.date == today_str)\
                                         .filter(AccountDailyCheck.check_type == check_type)\
                                         .with_lockmode('update').first()
    if check_type == CHECK_TYPE.DAILY_SIGN and daily_check:
        raise AuthenticateError(status=StatusCode.REACH_LIMIT)
    if not daily_check:
        daily_check = AccountDailyCheck()
        daily_check.user_id = user_id
        daily_check.date = today_str
        daily_check.check_type = check_type
        daily_check.check_times = 0
    daily_check.check_times += 1
    daily_check.save(auto_commit=False)
    added_credit = 0
    if check_type == CHECK_TYPE.DAILY_SIGN:
        account_sign = AccountSign.query.filter(
            AccountSign.user_id == user_id).first()
        if not account_sign:
            account_sign = AccountSign()
            account_sign.user_id = user_id
        last_sign_at = account_sign.last_sign_at
        if last_sign_at:
            timedelta = (today.replace(hour=0, minute=0, second=0, microsecond=0) -
                last_sign_at.replace(hour=0, minute=0, second=0, microsecond=0))
            if timedelta == datetime.timedelta(1):
                account_sign.continuous_times += 1
            else:
                account_sign.continuous_times = 1
        else:
            account_sign.continuous_times = 1
        account_sign.last_sign_at = today
        account_sign.save(auto_commit=False)
        if account_sign.continuous_times == 1:
            added_credit = DAILY_SIGN_AWARDS[0] / 2
        elif account_sign.continuous_times == 2:
            added_credit = DAILY_SIGN_AWARDS[1] / 2
        elif account_sign.continuous_times > 2:
            added_credit = DAILY_SIGN_AWARDS[2] / 2
    elif check_type == CHECK_TYPE.DAILY_SHARE and daily_check.check_times == 1:
        added_credit = DAILY_SHARE_AWARD
    if added_credit > 0:
        account = Account.query.filter(Account.id == user_id).one()
        if not account.credit:
            account.credit = added_credit
        else:
            account.credit += added_credit
        account.save(auto_commit=False)
        credit_record = CreditRecord()
        credit_record.user_id = user_id
        credit_record.type = RECORD_TYPE.IN
        if check_type == CHECK_TYPE.DAILY_SIGN:
            credit_record.title = u"Poin Absensi"
        else:
            credit_record.title = u"Poin Bagikan"
        credit_record.amount = added_credit
        credit_record.balance = account.credit
        credit_record.save(auto_commit=False)
    orm.session.commit()
    _LOGGER.info('daily check, %s, add credit %s', check_type, added_credit)
    return added_credit


@sql_wrapper
def get_report(start_day):
    resp = {}
    end_day = start_day + datetime.timedelta(days=1)
    for k in 'share', 'sign':
        t = CHECK_TYPE.DAILY_SIGN if k == 'sign' else CHECK_TYPE.DAILY_SHARE
        count = orm.session.query(func.count(AccountDailyCheck.id)).filter(
            AccountDailyCheck.check_type == t).filter(
            AccountDailyCheck.created_at >= start_day).filter(
            AccountDailyCheck.created_at < end_day).scalar()
        resp[k] = count or 0
    return resp


@sql_wrapper
def get_signin_list(start_day):
    start_day -= datetime.timedelta(days=1)
    items = orm.session.query(
        AccountSign.continuous_times, func.count(AccountSign)).filter(
        AccountSign.last_sign_at >= start_day).filter(
        AccountSign.continuous_times <= 30).group_by(
        AccountSign.continuous_times).all()

    resp = []
    for item in items:
        resp.append(list(item))

    return sorted(resp, key=lambda t: t[0], reverse=True)


@sql_wrapper
def add_credit(user_id, added_credit, title):
    account = Account.query.filter(
        Account.id == user_id).with_lockmode('update').one()
    if not account.credit:
        account.credit = added_credit
    else:
        account.credit += added_credit
    account.save(auto_commit=False)
    credit_record = CreditRecord()
    credit_record.user_id = user_id
    credit_record.type = RECORD_TYPE.IN
    credit_record.title = title
    credit_record.amount = added_credit
    credit_record.balance = account.credit
    credit_record.save(auto_commit=False)
    orm.session.commit()


def add_credit_in_transaction(user_id, added_credit, title):
    account = Account.query.filter(
        Account.id == user_id).with_lockmode('update').one()
    if not account.credit:
        account.credit = added_credit
    else:
        account.credit += added_credit
    account.save(auto_commit=False)
    credit_record = CreditRecord()
    credit_record.user_id = user_id
    credit_record.type = RECORD_TYPE.IN
    credit_record.title = title
    credit_record.amount = added_credit
    credit_record.balance = account.credit
    credit_record.save(auto_commit=False)


def add_consume_credit(user_id, consume_amount):
    added_credit = int(consume_amount) * AWARD_CREDIT_UNIT
    add_credit(user_id, added_credit, u"Pakai Poin")
    _LOGGER.info('check consume credit, add credit %s', added_credit)


def add_special_recharge_award_credit(user_id, amount):
    add_credit(user_id, amount, u"Isi Ulang")
    _LOGGER.info('add special recharge award credit: %s', amount)


def add_register_credit(user_id):
    add_credit(user_id, _REGISTER_CREDIT_AMOUNT, u"Daftar Poin")
    _LOGGER.info('add register award credit: %s', _REGISTER_CREDIT_AMOUNT)


def add_show_credit(user_id, show_id):
    show = get_show_by_id(show_id)
    activity = get_activity(None, show.template_id, show.term_number)
    credit_amount = activity.target_amount * _SHOW_AWARD_RATIO
    add_credit(user_id, credit_amount, u"Testimonial Poin")
    _LOGGER.info('add show award credit: %s', credit_amount)


def add_miss_return_credit(user_id, amount):
    add_credit(user_id, amount, u"Tidak menang, koin dikembalikan")
    _LOGGER.info('add miss return credit: %s', amount)


def add_invitation_credit(user_id):
    add_credit(user_id, _INVITATION_CREDIT_AMOUNT, u"Undang Teman")
    _LOGGER.info('add invitation credit: %s', _INVITATION_CREDIT_AMOUNT)


def add_referrer_credit(user_id, amount):
    add_credit(user_id, amount, u"Dapat 10x poin dari jumlah topup teman")
    _LOGGER.info('add referrer credit: %s', amount)


@sql_wrapper
def exchange_credit(user_id):
    account = Account.query.filter(
        Account.id == user_id).with_lockmode('update').one()
    if account.credit and account.credit / 1000 > 0:
        exchanged_credit = (account.credit / 1000) * 1000
        account.credit -= exchanged_credit
        added_price = exchanged_credit / 1000
        account.balance += added_price
        credit_record = CreditRecord()
        credit_record.user_id = user_id
        credit_record.type = RECORD_TYPE.EXCHANGE
        credit_record.title = u"Tukar ke Koin"
        credit_record.amount = -exchanged_credit
        credit_record.balance = account.credit
        credit_record.save(auto_commit=False)
        transaction = Transaction()
        transaction.id = id_generator.generate_long_id('transaction')
        transaction.user_id = user_id
        transaction.type = TRANSACTION_TYPE.AWARD
        transaction.title = u"Tukar ke Koin"
        transaction.price = added_price
        transaction.balance = account.balance
        transaction.status = TRANSACTION_STATUS.DONE
        transaction.save(auto_commit=False)
        orm.session.commit()
        _LOGGER.info(
            '%s exchange %s credit to %s', user_id, exchanged_credit, added_price)
        return exchanged_credit, added_price
    else:
        raise DataError('credit insufficient')


@sql_wrapper
def get_latest_distribution_term():
    return DistributeTerm.query.order_by(DistributeTerm.id.desc()).first()


@sql_wrapper
def get_latest_distribution(term_id):
    return DistributeRecord.query.filter(DistributeRecord.term_id == term_id).all()
