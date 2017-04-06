# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime, timedelta

from future.utils import raise_with_traceback
from sqlalchemy import func, text

from luckycommon.model import orm, slave
from luckycommon.model.stock import Goods
from luckycommon.account.model.account import Account
from luckycommon.model.category import CategoryActivity
from luckycommon.order.model.order import *
from luckycommon.model.activity import *
from luckycommon.db.helper import (parse_query_dct,
                                   generate_filter, get_orderby, paginate)
from luckycommon.cache import redis_cache
from luckycommon.utils import id_generator
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.exceptions import (DbError, DataError,
                                          ParamError, ResourceNotFound,
                                          ResourceInsufficient)
from luckycommon.utils.orm import get_count
from luckycommon.third.lottery import calc_announce_delay
from luckycommon.utils.tz import (format_seconds, get_utc_date, local_now,
                                  now_ts, adjust_ts, local_to_utc)

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def _fill_order(activity):
    try:
        pool_flag = redis_cache.check_numbers_pool(activity.id)
        if pool_flag:
            activity.current_amount = activity.target_amount - \
                redis_cache.get_left_numbers_count(activity.id)
        else:
            activity.current_amount = redis_cache.get_lucky_numbers_count(
                activity.id)
    except Exception:
        payed_orders = Order.query.filter(Order.activity_id == activity.id)\
                                  .filter(Order.status >= ORDER_STATUS.PAYED)\
                                  .all()
        sum = 0
        for order in payed_orders:
            sum += order.goods_quantity
        activity.current_amount = sum


@sql_wrapper
def get_activity(activity_id, template_id=None,
                 term_number=None, need_fill=True):
    if activity_id:
        activity = Activity.query.filter(Activity.id == activity_id).first()
    else:
        activity = Activity.query.filter(
            Activity.template_id == template_id).filter(
            Activity.term_number == term_number).first()
    if not activity:
        return None
    if need_fill:
            # fill current_amount
        _fill_order(activity)
    return activity


def get_winner_id(activity_id):
    ua = orm.session.query(ActivityWin.winner).filter(
        ActivityWin.activity_id == activity_id).scalar()
    return ua


@sql_wrapper
def get_hot_activity_count():
    return orm.session.query(orm.func.count(HotActivity.id)).scalar() or 0


@sql_wrapper
def get_buy_process():
    amount = orm.session.query(orm.func.sum(HotActivity.current_amount),
                               orm.func.sum(HotActivity.target_amount)).first()
    if not amount[0] or not amount[1]:
        return 0
    return round(float(amount[0]) / float(amount[1]), 4)


@sql_wrapper
def get_activitys_by_template(template_id, limit=0, offset=0):
    activitys = Activity.query.filter(
        Activity.template_id == template_id)
    total_count = get_count(activitys)

    return activitys.all(), total_count


@sql_wrapper
def get_activitys_by_ids(id_list, status=None, limit=0, offset=0, need_fill=True):
    """
    调用此接口要保证id_list长度不宜过大
    """
    if not id_list:
        return []
    query = Activity.query.filter(Activity.id.in_(id_list))
    if status is not None:
        junction = orm.or_
        status_filters = []
        if status & ACTIVITY_STATUS.STARTED:
            status_filters.append(Activity.status == ACTIVITY_STATUS.STARTED)
        if status & ACTIVITY_STATUS.ANNOUNCE_READY:
            status_filters.append(
                Activity.status == ACTIVITY_STATUS.ANNOUNCE_READY)
        if status & ACTIVITY_STATUS.ANNOUNCED:
            status_filters.append(Activity.status == ACTIVITY_STATUS.ANNOUNCED)
        if status & ACTIVITY_STATUS.EXPIRED:
            status_filters.append(Activity.status == ACTIVITY_STATUS.EXPIRED)
        query = query.filter(junction(*status_filters))
    query = query.order_by(Activity.status).order_by(
        Activity.updated_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    activitys = query.all()
    if need_fill:
        for activity in activitys:
            # fill current_amount
            _fill_order(activity)
    return activitys


def update_activity_status(activity_id, status):
    try:
        Activity.query.filter(Activity.id == activity_id).update(
            {'status': status})
        orm.session.commit()
    except Exception as e:
        _LOGGER.error('change activity status error, %s' % e)
        orm.session.rollback()
    finally:
        orm.session.close()


def create_user_activity(user_id, activity_id, numbers):
    try:
        user_activity = UserActivity.query.filter(
            UserActivity.user_id == user_id).filter(
            UserActivity.activity_id == activity_id).with_lockmode(
            'update').first()
        if not user_activity:
            user_activity = UserActivity()
            user_activity.user_id = user_id
            user_activity.activity_id = activity_id
            user_activity.numbers = ','.join(numbers)
            user_activity.save()
            _LOGGER.info('create user activity success: %s' % user_activity.id)
        else:
            old_numbers = [] if not user_activity.numbers else\
                user_activity.numbers.split(',')
            numbers.extend(old_numbers)
            user_activity.numbers = ','.join(numbers)
            orm.session.commit()
            _LOGGER.info('update user activity success: %s' % user_activity.id)
    except Exception as e:
        _LOGGER.exception('create/update user activity fail.')
        orm.session.rollback()
        raise_with_traceback(
            DbError('create/update user activity fail.(%s)' % e))
    finally:
        orm.session.close()

    return user_activity


@sql_wrapper
def get_user_activity(user_id, activity_id):
    query = UserActivity.query.filter(UserActivity.user_id == user_id)\
                              .filter(UserActivity.activity_id == activity_id)
    return query.first()


@sql_wrapper
def update_ua_status(activity_id, updated_status):
    UserActivity.query.filter(
        UserActivity.activity_id == activity_id).update({
            'status': updated_status,
            'updated_at': datetime.utcnow()
        })
    orm.session.commit()


@sql_wrapper
def get_first_user_activity(user_id):
    return UserActivity.query.filter(UserActivity.user_id == user_id).order_by(UserActivity.updated_at).first()


@sql_wrapper
def get_user_activities(user_id, only_win=False, status=None,
                        limit=0, offset=0):
    """
    目前会一次性取所有的参与记录，后面可以把user_activitys放到cache中
    并标示用户是否中奖
    """
    id_list = []
    if only_win:
        winned_activitys = redis_cache.get_winn_list(user_id)
        if winned_activitys:
            id_list.extend(winned_activitys)
        else:
            for win_activity in ActivityWin.query.filter(ActivityWin.winner == int(user_id)).all():
                id_list.append(win_activity.activity_id)
        count = len(id_list)
        activitys = get_activitys_by_ids(id_list, status, limit, offset)
    else:
        query = orm.session.query(UserActivity.activity_id).filter(
            UserActivity.user_id == user_id)
        if status is not None:
            junction = orm.or_
            status_filters = []
            if status & ACTIVITY_STATUS.STARTED or status & ACTIVITY_STATUS.ANNOUNCE_READY:
                status_filters.append(
                    UserActivity.status == ACTIVITY_STATUS.STARTED)
            if status & ACTIVITY_STATUS.ANNOUNCED:
                status_filters.append(
                    UserActivity.status == ACTIVITY_STATUS.ANNOUNCED)
            query = query.filter(junction(*status_filters))
        query = query.order_by(UserActivity.status).order_by(
            UserActivity.updated_at.desc())
        if limit > 0:
            query = query.limit(limit)
        if offset > 0:
            query = query.offset(offset)
        items = query.all()
        for item in items:
            id_list.append(item[0])
        count = len(id_list)
        activitys = get_activitys_by_ids(id_list, status=None)

    return activitys, count


@sql_wrapper
def get_activity_users(activity_id):
    query = UserActivity.query.filter(UserActivity.activity_id == activity_id)
    return query.all()


@sql_wrapper
def get_all_activitys(limit=0, offset=0, unit=None, status=None):
    query = Activity.query
    if unit is not None:
        query = query.filter(Activity.unit == unit)
    if status is not None:
        junction = orm.or_
        status_filters = []
        if status & ACTIVITY_STATUS.STARTED:
            status_filters.append(Activity.status == ACTIVITY_STATUS.STARTED)
        if status & ACTIVITY_STATUS.ANNOUNCE_READY:
            status_filters.append(
                Activity.status == ACTIVITY_STATUS.ANNOUNCE_READY)
        if status & ACTIVITY_STATUS.ANNOUNCED:
            status_filters.append(Activity.status == ACTIVITY_STATUS.ANNOUNCED)
        if status & ACTIVITY_STATUS.EXPIRED:
            status_filters.append(Activity.status == ACTIVITY_STATUS.EXPIRED)
        query = query.filter(junction(*status_filters))

    query = query.order_by(Activity.status).order_by(
        Activity.updated_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    activitys = query.all()
    for activity in activitys:
        # fill current_amount
        if activity.status & ACTIVITY_STATUS.STARTED:
            _fill_order(activity)

    return activitys, len(activitys)


BMW_LIST = [774, 775,]


def adjust_hot_activitys(activity_list):
    """
    adjust sort by percentage for page 1
    """
    priority_list = []
    unpriority_list = []
    count = 0
    for activity in activity_list:
        count += 1
        target_amount = activity.target_amount
        current_amount = activity.current_amount
        if (activity.price == 0 or
            float(current_amount) / target_amount > 0.6 or
                activity.template_id in BMW_LIST):
            priority_list.append(activity)
        else:
            unpriority_list.append(activity)
    priority_list.extend(unpriority_list)
    return priority_list


@sql_wrapper
def get_hot_activitys(limit=0, offset=0, unit=None, status=None):
    query = HotActivity.query
    if unit is not None:
        query = query.filter(HotActivity.unit == unit)
    if status is not None:
        query = query.filter(HotActivity.status == status)

    query = query.order_by(HotActivity.hot.desc())
    if limit > 0:
        query = query.limit(limit)
    query = query.offset(offset)
    hot_activitys = query.all()
    hot_dict = {}
    for activity in hot_activitys:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (activity.template_id, activity.term_number))
        hot_dict[activity_id] = activity.hot

    activity_list = []
    if hot_dict:
        activitys = Activity.query.filter(
            Activity.id.in_(hot_dict.keys())).all()
        for activity in activitys:
            _fill_order(activity)
            activity_list.append(
                {'data': activity, 'hot': hot_dict[activity.id]})

    activity_list.sort(key=lambda x: x.get('hot'), reverse=True)
    activity_list = [activity['data'] for activity in activity_list]
    # adjust sort by percentage for page 1
    if offset == 0:
        activity_list = adjust_hot_activitys(activity_list)

    return activity_list, len(activity_list)


@sql_wrapper
def get_hot_activitys_by_tids(tids, limit=0, offset=0):
    if not tids:
        return []
    query = HotActivity.query.filter(HotActivity.template_id.in_(tids))
    query = query.order_by(HotActivity.hot.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    hot_activitys = query.all()
    hot_dict = {}
    for activity in hot_activitys:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (activity.template_id, activity.term_number))
        hot_dict[activity_id] = activity.hot

    activity_list = []
    if hot_dict:
        activitys = Activity.query.filter(
            Activity.id.in_(hot_dict.keys())).all()
        for activity in activitys:
            _fill_order(activity)
            activity_list.append(
                {'data': activity, 'hot': hot_dict[activity.id]})

    activity_list.sort(key=lambda x: x.get('hot'), reverse=True)
    activity_list = [activity['data'] for activity in activity_list]
    # adjust sort by percentage for page 1
    if offset == 0:
        activity_list = adjust_hot_activitys(activity_list)

    return activity_list


@sql_wrapper
def get_left_activitys(limit=0, offset=0, unit=None, status=None):
    """
    获取最少剩余的活动
    """
    query = HotActivity.query
    if unit is not None:
        query = query.filter(HotActivity.unit == unit)
    if status is not None:
        query = query.filter(HotActivity.status == status)

    query = query.order_by(HotActivity.left_amount)
    if limit > 0:
        query = query.limit(limit)
    query = query.offset(offset)
    left_activitys = query.all()
    left_dict = {}
    for activity in left_activitys:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (activity.template_id, activity.term_number))
        left_dict[activity_id] = activity.left_amount

    activity_list = []
    if left_dict:
        activitys = Activity.query.filter(
            Activity.id.in_(left_dict.keys())).all()
        for activity in activitys:
            _fill_order(activity)
            activity_list.append(
                {'data': activity, 'left': left_dict[activity.id]})

    activity_list.sort(key=lambda x: x.get('left'), reverse=False)
    activity_list = [activity['data'] for activity in activity_list]

    return activity_list, len(activity_list)


@sql_wrapper
def get_left_activitys_by_tids(tids, limit=0, offset=0):
    if not tids:
        return []
    query = HotActivity.query.filter(HotActivity.template_id.in_(tids))
    query = query.order_by(HotActivity.left_amount)
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    left_activitys = query.all()
    left_dict = {}
    for activity in left_activitys:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (activity.template_id, activity.term_number))
        left_dict[activity_id] = activity.left_amount

    activity_list = []
    if left_dict:
        activitys = Activity.query.filter(
            Activity.id.in_(left_dict.keys())).all()
        for activity in activitys:
            _fill_order(activity)
            activity_list.append(
                {'data': activity, 'left': left_dict[activity.id]})

    activity_list.sort(key=lambda x: x.get('left'), reverse=False)
    activity_list = [activity['data'] for activity in activity_list]

    return activity_list


@sql_wrapper
def get_latest_activitys(limit=0, offset=0, unit=None, status=None):
    """
    获取最新上架的活动
    """
    query = HotActivity.query
    if unit is not None:
        query = query.filter(HotActivity.unit == unit)
    if status is not None:
        query = query.filter(HotActivity.status == status)

    query = query.order_by(HotActivity.added_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    latest_activitys = query.all()
    latest_dict = {}
    for activity in latest_activitys:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (activity.template_id, activity.term_number))
        latest_dict[activity_id] = activity.added_at

    activity_list = []
    if latest_dict:
        activitys = Activity.query.filter(
            Activity.id.in_(latest_dict.keys())).all()
        for activity in activitys:
            _fill_order(activity)
            activity_list.append(
                {'data': activity, 'added_at': latest_dict[activity.id]})

    activity_list.sort(key=lambda x: x.get('added_at'), reverse=True)
    activity_list = [activity['data'] for activity in activity_list]

    return activity_list, len(activity_list)


@sql_wrapper
def get_latest_activitys_by_tids(tids, limit=0, offset=0):
    if not tids:
        return []
    query = HotActivity.query.filter(HotActivity.template_id.in_(tids))
    query = query.order_by(HotActivity.added_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    latest_activitys = query.all()
    latest_dict = {}
    for activity in latest_activitys:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (activity.template_id, activity.term_number))
        latest_dict[activity_id] = activity.added_at

    activity_list = []
    if latest_dict:
        activitys = Activity.query.filter(
            Activity.id.in_(latest_dict.keys())).all()
        for activity in activitys:
            _fill_order(activity)
            activity_list.append(
                {'data': activity, 'added_at': latest_dict[activity.id]})

    activity_list.sort(key=lambda x: x.get('added_at'), reverse=True)
    activity_list = [activity['data'] for activity in activity_list]

    return activity_list


@sql_wrapper
def get_costly_activitys(limit=0, offset=0, cost_reverse=True,
                         unit=None, status=None):
    """
    获取最贵/便宜的活动
    """
    query = HotActivity.query
    if unit is not None:
        query = query.filter(HotActivity.unit == unit)
    if status is not None:
        query = query.filter(HotActivity.status == status)

    if cost_reverse:
        query = query.order_by(HotActivity.target_amount.desc())
    else:
        query = query.order_by(HotActivity.target_amount)
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    costly_activitys = query.all()
    costly_dict = {}
    for activity in costly_activitys:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (activity.template_id, activity.term_number))
        costly_dict[activity_id] = activity.target_amount

    activity_list = []
    if costly_dict:
        activitys = Activity.query.filter(
            Activity.id.in_(costly_dict.keys())).all()
        for activity in activitys:
            _fill_order(activity)
            activity_list.append(
                {'data': activity, 'cost': costly_dict[activity.id]})

    if cost_reverse:
        activity_list.sort(key=lambda x: x.get('cost'), reverse=True)
    else:
        activity_list.sort(key=lambda x: x.get('cost'), reverse=False)
    activity_list = [activity['data'] for activity in activity_list]

    return activity_list, len(activity_list)


@sql_wrapper
def get_costly_activitys_by_tids(tids, cost_reverse=True, limit=0, offset=0):
    if not tids:
        return []
    query = HotActivity.query.filter(HotActivity.template_id.in_(tids))
    if cost_reverse:
        query = query.order_by(HotActivity.target_amount.desc())
    else:
        query = query.order_by(HotActivity.target_amount)
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    costly_activitys = query.all()
    costly_dict = {}
    for activity in costly_activitys:
        activity_id = id_generator.generate_uuid(
            'activity:%s:%s' % (activity.template_id, activity.term_number))
        costly_dict[activity_id] = activity.target_amount

    activity_list = []
    if costly_dict:
        activitys = Activity.query.filter(
            Activity.id.in_(costly_dict.keys())).all()
        for activity in activitys:
            _fill_order(activity)
            activity_list.append(
                {'data': activity, 'cost': costly_dict[activity.id]})

    if cost_reverse:
        activity_list.sort(key=lambda x: x.get('cost'), reverse=True)
    else:
        activity_list.sort(key=lambda x: x.get('cost'), reverse=False)
    activity_list = [activity['data'] for activity in activity_list]

    return activity_list


@sql_wrapper
def get_new_activitys(limit=0, offset=0, unit=None, status=None):
    query = Activity.query.filter(Activity.status == ACTIVITY_STATUS.STARTED)
    if unit is not None:
        query = query.filter(Activity.unit == unit)

    query = query.order_by(Activity.created_at.desc())
    if limit > 0:
        query = query.limit(limit)
    query = query.offset(offset)
    activitys = query.all()
    for activity in activitys:
            # fill current_amount
        _fill_order(activity)

    return activitys, len(activitys)


@sql_wrapper
def get_revealed_activitys(limit, offset, template_id):
    query = Activity.query.filter(
        Activity.status == ACTIVITY_STATUS.ANNOUNCED) .filter(
        Activity.template_id == template_id)
    query = query.order_by(Activity.updated_at.desc())

    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    activitys = query.all()
    # for activity in activitys:
    #        # fill current_amount
    #    _fill_order(activity)

    return activitys, len(activitys)


@sql_wrapper
def get_activity_win(activity_id):
    return ActivityWin.query.filter(
        ActivityWin.activity_id == activity_id).first()


@sql_wrapper
def update_activity_win(activity_id, info):
    announce_info = json.dumps(info, ensure_ascii=False)
    ActivityWin.query.filter(
        ActivityWin.activity_id == activity_id).update({
            'announce_info': announce_info,
            'updated_at': datetime.utcnow()
        })
    orm.session.commit()


@sql_wrapper
def get_latest_term(template_id):
    template = ActivityTemplate.query.filter(
        ActivityTemplate.id == template_id).one()
    return template.current_term


@sql_wrapper
def list_templates(query_dct):
    category_id = query_dct.pop('category_id', None)
    query = ActivityTemplate.query
    if category_id is not None:
        query = query.join(
            CategoryActivity,
            ActivityTemplate.id == CategoryActivity.template_id).filter(
            CategoryActivity.category_id == category_id)

    query_dct = parse_query_dct(query_dct, ActivityTemplate)
    query = query.filter(generate_filter(query_dct, ActivityTemplate))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), ActivityTemplate)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)
    return query.all(), total_count


@sql_wrapper
def list_activities(query_dct):
    winner_id = query_dct.pop('winner_id', None)
    winner_type = int(query_dct.pop('winner_type', 0))
    status = int(query_dct.get('status', -1))
    query_dct = parse_query_dct(query_dct, Activity)
    if status >= ACTIVITY_STATUS.ANNOUNCED:
        query = orm.session.query(
            Activity, ActivityWin.winner.label('i'), Account.is_virtual).join(
            ActivityWin, Activity.id == ActivityWin.activity_id).join(
            Account, ActivityWin.winner == Account.id)
    else:
        query = orm.session.query(
            Activity, ActivityWin.winner.label('i'),
            Account.is_virtual).outerjoin(
            ActivityWin, Activity.id == ActivityWin.activity_id).outerjoin(
            Account, ActivityWin.winner == Account.id)
    if winner_id:
        winner_id = long(winner_id)
        query = query.filter(ActivityWin.winner == winner_id)
    if winner_type and not winner_id:
        # 1: real, 2: virtual
        if winner_type == 1:
            query = query.filter(Account.is_virtual == False)
        elif winner_type == 2:
            query = query.filter(Account.is_virtual == True)
    query = query.filter(generate_filter(query_dct, Activity))
    total_count = get_count(query)
    orderby_str = query_dct.get('$orderby')
    orderby = get_orderby(orderby_str, Activity)
    if orderby is not None:
        query = query.order_by(orderby)
    elif orderby_str == 'buy_time':
        # 买满时长
        query = query.order_by(func.timestampdiff(
            text('SECOND'),
            Activity.created_at, Activity.announced_at))
    elif orderby_str == '-buy_time':
        query = query.order_by(func.timestampdiff(
            text('SECOND'), Activity.created_at, Activity.announced_at
        ).desc())
    query = paginate(query, query_dct)
    return query.all(), total_count


@sql_wrapper
def calc_prices(start_day=None, end_day=None):
    overview = {
        'ongoing_price': 0,
        'announce_ready_price': 0,
        'announced_price': 0,
        'total_balance': 0.00,
        'announced_buy_cost': 0,
        'announced_earn': 0
    }
    virtual_account = redis_cache.get_virtual_account()
    current_ac = Activity.query.filter(Activity.status.in_(
        [ACTIVITY_STATUS.STARTED, ACTIVITY_STATUS.ANNOUNCE_READY])).all()
    for ac in current_ac:
        nums = orm.session.query(UserActivity.numbers).join(
            Account, Account.id == UserActivity.user_id).filter(
            UserActivity.activity_id == ac.id).filter(
            Account.is_virtual == False).all()
        for num in nums:
            price = (len(num[0]) + 1) / 9
            if ac.status == ACTIVITY_STATUS.STARTED:
                overview['ongoing_price'] += price
            else:
                overview['announce_ready_price'] += price

    if start_day is None:
        start_day = get_utc_date()
        end_day = start_day + timedelta(days=1)
    announced_ac = Activity.query.filter(
        Activity.status == ACTIVITY_STATUS.ANNOUNCED).filter(
        Activity.announced_at >= start_day).filter(
        Activity.announced_at < end_day).all()
    for ac in announced_ac:
        nums = orm.session.query(UserActivity.numbers).join(
            Account, Account.id == UserActivity.user_id).filter(
            UserActivity.activity_id == ac.id).filter(
            Account.is_virtual == False).all()
        price = cost = 0
        for num in nums:
            price += (len(num[0]) + 1) / 9
        overview['announced_price'] += price
        winner = get_winner_id(ac.id)
        if str(winner) not in virtual_account:
            cost = float(orm.session.query(Goods.price).filter(
                Goods.id == ac.goods_id).scalar())
            overview['announced_buy_cost'] += cost
        overview['announced_earn'] += price - cost

    overview['total_balance'] = float(orm.session.query(
        func.sum(Account.balance)).filter(
        Account.is_virtual == False).scalar())

    return overview


@sql_wrapper
def get_activities_overview():
    overview = {}
    overview['buy_process'] = get_buy_process()
    today = get_utc_date()
    r = orm.session.query(func.count(Activity.id), func.sum(
        func.timestampdiff(text('SECOND'), Activity.created_at,
                           Activity.announced_at)))
    ready = r.filter(Activity.status == ACTIVITY_STATUS.ANNOUNCE_READY).first()
    announced = r.filter(Activity.status == ACTIVITY_STATUS.ANNOUNCED).filter(
        Activity.created_at >= today).first()
    overview['announce_ready_count'] = ready[0] if ready and ready[0] else 0
    overview['announced_count'] = announced[0] if announced and announced[
        0] else 0
    count = overview['announce_ready_count'] + overview['announced_count']
    total_buy_time = ready[1] if overview['announce_ready_count'] else 0
    total_buy_time += announced[1] if overview['announced_count'] else 0
    total_buy_time -= count * calc_announce_delay()
    overview['average_buy_time'] = format_seconds(
        total_buy_time / count) if count else 0
    overview['ongoing_count'] = orm.session.query(
        func.count(HotActivity.id)).scalar()

    return overview


def _get_top_count(start_day=None, end_day=None):
    result = []
    query = orm.session.query(
        Activity.template_id, func.count(Activity).label("c")).filter(
        Activity.status == ACTIVITY_STATUS.ANNOUNCED)
    if start_day:
        query = query.filter(Activity.announced_at >= start_day)
    if end_day:
        query = query.filter(Activity.announced_at < end_day)
    query = query.group_by(Activity.template_id)
    query = query.order_by("c desc").limit(5)
    for k in query.all():
        template_id, count = k
        temp = orm.session.query(
            ActivityTemplate.name, ActivityTemplate.short_title).filter(
            ActivityTemplate.id == template_id).first()
        if temp:
            name, short_title = temp
        else:
            short_title = '(template missed...)'
        result.append({
            "template_id": template_id,
            "name": short_title or name,
            "count": count
        })

    return result


def _get_average_buy_time(start_day=None, end_day=None, template_id=None,
                          return_origin=False):
    query = orm.session.query(func.count(Activity.id), func.sum(
        func.timestampdiff(
            text('SECOND'),
            Activity.created_at, Activity.announced_at))).filter(
        Activity.status == ACTIVITY_STATUS.ANNOUNCED)
    if template_id:
        query = query.filter(Activity.template_id == template_id)
    if start_day:
        query = query.filter(Activity.created_at >= start_day)
    if end_day:
        query = query.filter(Activity.created_at < end_day)
    k = query.first()
    if k and k[0]:
        k = list(k)
        k[1] = float(k[1])
        k[1] -= k[0] * calc_announce_delay()
    if return_origin:
        return k or [0, 0]
    else:
        return k[1] / k[0] if k[0] else 0


@sql_wrapper
def get_activity_report(start_day, end_day, cached):
    report = {}
    if "last_day_announced_count" not in cached:
        report["last_day_announced_count"] = orm.session.query(
            func.count(Activity.id)).filter(
            Activity.status == ACTIVITY_STATUS.ANNOUNCED).filter(
            Activity.announced_at >= start_day).filter(
            Activity.announced_at < end_day).scalar() or 0
    if "last_day_real_winner_count" not in cached:
        report["last_day_real_winner_count"] = orm.session.query(
            func.count(ActivityWin.activity_id)).join(
            Account, ActivityWin.winner == Account.id).filter(
            ActivityWin.created_at >= start_day).filter(
            ActivityWin.created_at < end_day).filter(
            Account.is_virtual == False).scalar() or 0

    if "last_day_virtual_buy_amount" not in cached:
        real = cached.get("last_day_real_buy_amount", 0)
        total = orm.session.query(
            func.sum(Order.total_price)).filter(
            Order.created_at >= start_day).filter(
            Order.created_at < end_day).scalar()
        report['last_day_virtual_buy_amount'] = int(total or 0) - real

    if 'last_day_buy_dist' not in cached:
        report['last_day_buy_dist'] = {
            'hours': [],
            'virtual': [],
            'real': []
        }
        hours = set()
        dist = {
            'virtual': {},
            'real': {}
        }
        for k in (False, True):
            t = 'virtual' if k else 'real'
            items = orm.session.query(
                func.hour(Order.created_at), func.sum(Order.total_price)).join(
                Account, Account.id == Order.buyer).filter(
                Account.is_virtual == k).filter(
                Order.created_at >= start_day).filter(
                Order.created_at < end_day).group_by(
                func.hour(Order.created_at)).all()
            for h, p in items:
                # for beijing timezone only
                h = h + 8
                if h >= 24:
                    h = h - 24
                hours.add(h)
                dist[t][h] = int(float(p))
        hours = sorted(list(hours))
        for h in hours:
            for k in 'virtual', 'real':
                report['last_day_buy_dist'][k].append(dist[k].get(h, 0))
        report['last_day_buy_dist']['hours'] = hours

    for k in 'day', 'week':
        key = 'last_%s_real_buy_top10' % k
        start = start_day if k == 'day' else end_day - timedelta(days=7)

        if key not in cached:
            report[key] = []
            items = orm.session.query(
                Activity.template_id,
                func.sum(Order.total_price).label('s')).select_from(
                Order).join(Account, Account.id == Order.buyer).join(
                Activity, Activity.id == Order.activity_id).filter(
                Account.is_virtual == False).filter(
                Order.created_at >= start).filter(
                Order.created_at < end_day).group_by(
                Activity.template_id).order_by(
                's desc').limit(10).all()
            for template_id, amount in items:
                template = get_template(template_id)
                template_name = template.short_title or template.name\
                    if template else u'...'
                report[key].append({
                    'template_id': template_id,
                    'template_name': template_name,
                    'amount': int(float(amount))
                })

    if "average_buy_time_list" not in cached:
        report["average_buy_time_list"] = []
        for k in ((1, 0), (7, None), (30, None), (None, None)):
            start = end = None
            if k[0] is not None:
                start = end_day - timedelta(days=k[0])
            if k[1] is not None:
                end = end_day - timedelta(days=k[1])
            if k[0] and k[0] < 30:
                key = "last_%s_day_announced_top5" % k[0]
                report[key] = _get_top_count(start, end)
            report["average_buy_time_list"].append(
                _get_average_buy_time(start, end))
    report.update(cached)
    return report


@sql_wrapper
def get_money_report(start_day, useable_cache=None, day=''):
    report = {
        "last_day_payed": 0,
        "last_day_cost": 0,
        "win_cost_dist": [0, 0, 0, 0, 0]
    }
    end_day = get_utc_date(start_day)
    start_day = end_day - timedelta(days=1)

    vas = redis_cache.get_virtual_account()
    last_day_announced_acs = orm.session.query(Activity).filter(
        Activity.status == ACTIVITY_STATUS.ANNOUNCED).filter(
        Activity.announced_at >= start_day).filter(
        Activity.announced_at < end_day).all()
    for ac in last_day_announced_acs:
        real_buy = orm.session.query(
            func.sum((func.length(UserActivity.numbers) + 1) / 9)).join(
            Account, UserActivity.user_id == Account.id).filter(
            UserActivity.activity_id == ac.id).filter(
            Account.is_virtual == False).scalar()
        report["last_day_payed"] += float(real_buy or 0)
        winner = get_winner_id(ac.id)
        if str(winner) not in vas:
            cost = orm.session.query(
                Goods.price).filter(Goods.id == ac.goods_id).scalar()
            report["last_day_cost"] += float(cost or 0)

    # the following will be very slow, so use the cache as much as possible
    cached_day = None
    if useable_cache:
        cached_day = datetime.strptime(day, '%Y-%m-%d') + timedelta(days=1)
        cached_day = local_to_utc(cached_day).replace(tzinfo=None)
        report["win_cost_dist"] = useable_cache["win_cost_dist"]
    query = orm.session.query(
        ActivityWin.activity_id, ActivityWin.winner).join(
        Account, Account.id == ActivityWin.winner).filter(
        Account.is_virtual == False)
    if useable_cache:
        query = query.filter(ActivityWin.created_at >= cached_day)
    items = query.all()
    for item in items:
        activity_id, winner = item
        winner_cost = orm.session.query(
            (func.length(UserActivity.numbers) + 1) / 9).filter(
            UserActivity.activity_id == activity_id).filter(
            UserActivity.user_id == winner).scalar()
        winner_cost = int(float(winner_cost or 0))
        if winner_cost == 1:
            report['win_cost_dist'][0] += 1
        elif 11 > winner_cost > 1:
            report['win_cost_dist'][1] += 1
        elif 101 > winner_cost > 10:
            report['win_cost_dist'][2] += 1
        elif 1001 > winner_cost > 100:
            report['win_cost_dist'][3] += 1
        else:
            report['win_cost_dist'][4] += 1

    return report


@sql_wrapper
def get_activity_stats(template_id, date):
    stats = {
        "announced_count_list": [],
        "average_buy_time_list": []
    }
    template = get_template(template_id)
    if not template:
        return stats
    today = get_utc_date(date)
    yesterday = today - timedelta(days=1)
    now = local_now()
    last_monday = get_utc_date((
        now - timedelta(days=now.weekday())).strftime('%Y-%m-%d'))
    last_month_1st = get_utc_date((now - timedelta(
        days=now.day - 1) if now.day != 1 else now).strftime('%Y-%m-%d'))
    first_start_day = template.added_at or template.created_at
    first_start_day = get_utc_date(first_start_day.strftime('%Y-%m-%d'))
    for k in [(yesterday, today), (last_monday, today),
              (last_month_1st, today), (first_start_day, today)]:
        t = _get_average_buy_time(k[0], k[1], template_id, True)
        stats['announced_count_list'].append(t[0] / ((k[1] - k[0]).days or 1))
        stats['average_buy_time_list'].append(t[1] / t[0] if t[0] else 0)
    return stats


@sql_wrapper
def get_start_time(template_id):
    return orm.session.query(Activity.created_at).filter(
        Activity.template_id == template_id).filter(
        Activity.term_number == 1).scalar()


@sql_wrapper
def get_template(template_id):
    template = ActivityTemplate.query.filter(
        ActivityTemplate.id == template_id).first()
    return template


@sql_wrapper
def get_cheap_template_ids():
    id_list = []
    templates = ActivityTemplate.query.filter(
        ActivityTemplate.status == TEMPLATE_STATUS.STARTED).filter(
        ActivityTemplate.buy_limit == 0).filter(
        ActivityTemplate.target_amount < 500).all()
    for template in templates:
        id_list.append(template.id)
    return id_list


@sql_wrapper
def get_tids_by_price(min_price=0, max_price=100):
    id_list = []
    templates = ActivityTemplate.query.filter(
        ActivityTemplate.status == TEMPLATE_STATUS.STARTED).filter(
        ActivityTemplate.target_amount <= max_price).filter(
        ActivityTemplate.target_amount >= min_price).all()
    for template in templates:
        id_list.append(template.id)
    return id_list


@sql_wrapper
def get_tids_by_aids(aids):
    items = Activity.query.filter(Activity.id.in_(aids)).all()
    return [item.template_id for item in items]


@sql_wrapper
def create_template(template):
    ac_template = ActivityTemplate()
    for k in ('name', 'desc', 'images', 'goods_id', 'cover',
              'price', 'unit', 'target_amount', 'country', 'graphics',
              'buy_limit', 'short_title', 'weight', 'pk'):
        if hasattr(template, k):
            setattr(ac_template, k, getattr(template, k))
    ac_template.current_term = 0
    ac_template.status = TEMPLATE_STATUS.START_READY
    ac_template.save()
    _LOGGER.info('create template success: %s' % ac_template.id)

    return ac_template


@sql_wrapper
def update_template(template_id, info):
    saved_template = ActivityTemplate.query.with_for_update().filter(
        ActivityTemplate.id == template_id).first()
    need_start = False
    if (saved_template and saved_template.status != TEMPLATE_STATUS.STARTED and
            info['status'] == TEMPLATE_STATUS.STARTED):
        need_start = True
        saved_template.added_at = datetime.utcnow()
    for k, v in info.iteritems():
        if hasattr(saved_template, k):
            setattr(saved_template, k, v)

    saved_template.save()
    return need_start


@sql_wrapper
def delete_template(template_id):
    t = ActivityTemplate.query.filter(
        ActivityTemplate.id == template_id).first()
    if t:
        t.delete()


def _internal_choose_pk_numbers(target_amount, pk, choose_size):
    choosed_numbers = []
    unit_size = target_amount / pk
    if 2 == pk:
        if 0 == choose_size:
            # small number
            choosed_numbers = range(1, unit_size + 1)
        else:
            # big number
            choosed_numbers = range(unit_size + 1, target_amount + 1)
    elif 3 == pk:
        if 0 == choose_size:
            # small number
            choosed_numbers = range(1, unit_size + 1)
        elif 2 == choose_size:
            # middle number
            choosed_numbers = range(unit_size + 1, unit_size * 2 + 1)
        else:
            # big number
            choosed_numbers = range(unit_size * 2 + 1, target_amount + 1)
    else:
        raise DbError('pk size invalid %s' % pk)
    return choosed_numbers


@sql_wrapper
def get_pk_info(activity):
    item = ActivityPK.query.filter(
        ActivityPK.activity_id == activity.id).first()
    return json.loads(item.pk_info) or {}


@sql_wrapper
def setup_pk_info(activity):
    item = ActivityPK()
    item.activity_id = activity.id
    item.target_amount = activity.target_amount
    item.pk = activity.pk
    if 2 == item.pk:
        pk_info = {0: None, 1: None}
    elif 3 == item.pk:
        pk_info = {0: None, 1: None, 2: None}
    else:
        raise ParamError('pk number invalid')
    item.pk_info = json.dumps(pk_info)
    item.save()


@sql_wrapper
def choose_pk_numbers(user_id, activity_id, choose_size):
    item = ActivityPK.query.filter(
        ActivityPK.activity_id == activity_id).with_lockmode('update').one()
    pk_info = json.loads(item.pk_info) or {}
    if str(choose_size) not in pk_info:
        raise ParamError('pk size invalid')
    size_info = pk_info[str(choose_size)]
    if size_info:
        raise ParamError('choosed by other')
    # choose number
    choosed_numbers = _internal_choose_pk_numbers(
        item.target_amount, item.pk, choose_size)
    ret = redis_cache.lock_numbers(activity_id, *choosed_numbers)
    if not ret:
        raise DbError('pk lock_numbers error %s' % (activity_id, choose_size))
    pk_info[str(choose_size)] = {
        'uid': user_id,
        'ts': now_ts()
    }
    item.pk_info = json.dumps(pk_info)
    item.save()
    return choosed_numbers


@sql_wrapper
def get_pk_latest_trend(activity):
    trend_list = []
    query = Activity.query.filter(
        Activity.status == ACTIVITY_STATUS.ANNOUNCED) .filter(
        Activity.template_id == activity.template_id)
    query = query.order_by(Activity.updated_at.desc())
    query = query.limit(10)
    activitys = query.all()
    unit_size = activity.target_amount / activity.pk
    if 2 == activity.pk:
        range_list = ((1, unit_size), (unit_size + 1, activity.target_amount))
    else:
        range_list = ((1, unit_size),
                      (unit_size + 1, unit_size * 2),
                      (unit_size * 2 + 1, activity.target_amount))
    for activity in activitys:
        lucky_number = activity.winner
        size_index = 0
        for i in range_list:
            n = int(lucky_number) - 10000000
            if n >= i[0] and n <= i[1]:
                break
            size_index += 1
        trend_list.append({
            'term': activity.term_number,
            'size': size_index,
            'lucky_number': lucky_number
        })

    return trend_list


@sql_wrapper
def get_pk_templates(pk=2, offset=0, limit=0):
    query = ActivityTemplate.query.filter(ActivityTemplate.status == TEMPLATE_STATUS.STARTED).filter(
        ActivityTemplate.pk == pk)
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    return query.all()


class ActivityStarter:

    """
    Provide transaction operation for creating activity
    """
    _MAX_TRY = 3

    @classmethod
    def __update_template(cls, template_id):
        template = ActivityTemplate.query.filter(
            ActivityTemplate.id == template_id).with_lockmode('update').first()
        template.current_term = template.current_term + 1
        return template

    @classmethod
    def __resume_activity(cls, exists_activity, template):
        exists_activity.resume(template)

    @classmethod
    def __start_activity(cls, template, insufficient=False):
        activity = Activity.next_from_template(
            template, insufficient=insufficient)
        activity.save(False)
        return activity

    @classmethod
    def start(cls, template_id, goods_id, exists_activity=None):
        """
        transaction operation below
        1. consume stock
        2. modify template status
        3. create activity
        """
        try_count = 1

        while try_count <= cls._MAX_TRY:
            goods = Goods.query.filter(Goods.id == goods_id).first()
            if not goods:
                raise_with_traceback(
                    ResourceNotFound("goods %s not exists" % goods_id))

            old_sold = goods.sold
            new_sold = old_sold + 1
            if new_sold > goods.total:
                raise_with_traceback(ResourceInsufficient(
                    "goods stock %s insufficient" % goods_id))

            try:
                # add `sold` filter to resolve cocurrency trouble
                res = Goods.query.filter(Goods.id == goods_id).filter(
                    Goods.sold == old_sold).update({'sold': new_sold})
                if not res:
                    _LOGGER.warn('coucurrency trouble when consume stock,'
                                 ' try count(%d)', try_count)
                    raise
                else:
                    # do transaction
                    template = cls.__update_template(template_id)
                    if exists_activity:
                        # resume exists activity
                        activity = cls.__resume_activity(
                            exists_activity, template)
                    else:
                        activity = cls.__start_activity(template)
                    orm.session.commit()
                    _LOGGER.info('start activity[%s] success' % activity.id)
                    return activity
            except Exception as e:
                try_count += 1
                orm.session.rollback()
                _LOGGER.exception(
                    'consume stock transaction operation exception.(%s)' % e)
            finally:
                orm.session.close()

        if try_count > cls._MAX_TRY:
            raise_with_traceback(
                DbError("cocurrency trouble when consume stock %s" % goods_id))

        # we can never get here
        return None


_ADJUST_LIMIT = 800  # 不能小于500


class ActivityAnnouncer:

    """
    Announce transaction operation
    1. update activity
    2. update order
    """
    @classmethod
    def __announce_activity(cls, activity, lucky_number):
        activity.winner = str(lucky_number)
        activity.status = ACTIVITY_STATUS.ANNOUNCED
        dt = datetime.utcnow()
        if activity.target_amount > _ADJUST_LIMIT:
            dt = adjust_ts(dt, delta_seconds=3)
        activity.announced_at = dt
        activity.save(auto_commit=False)

    @classmethod
    def __get_user_numbers(cls, user_id, activity_id):
        user_activity = UserActivity.query.filter(
            UserActivity.user_id == user_id).filter(
            UserActivity.activity_id == activity_id).first()
        if not user_activity or not user_activity.numbers:
            _LOGGER.error('user numbers blank!!! %s %s' %
                          (user_id, activity_id))
            return []
        return user_activity.numbers.split(',')

    @classmethod
    def __update_user_activity_status(cls, activity_id):
        UserActivity.query.filter(
            UserActivity.activity_id == activity_id).update({
                'status': ACTIVITY_STATUS.ANNOUNCED,
                'updated_at': datetime.utcnow()
            })

    @classmethod
    def __announce_win(cls, activity_id, lucky_number,
                       lucky_order, result_a, lottery, a_list):
        activity_win = ActivityWin()
        activity_win.activity_id = activity_id
        activity_win.lucky_number = lucky_number
        activity_win.winner = lucky_order.buyer
        activity_win.order_id = lucky_order.id
        lucky_user = Account.query.filter(
            Account.id == lucky_order.buyer).one()
        geo_info = {} if not lucky_order.extend else json.loads(
            lucky_order.extend)
        announce_info = {
            'result_a': result_a,
            'a_list': a_list,
            'result_b': lottery.number,
            'lottery_phase': lottery.phase,
            'lottery_reference': lottery.reference,
            'winner': {
                'uid': lucky_user.id,
                'avatar': lucky_user.avatar_id,
                'nick_name': lucky_user.nick_name,
                'ip': geo_info.get('ip'),
                'addr': geo_info.get('addr'),
                #'numbers': cls.__get_user_numbers(lucky_user.id, activity_id),
                'num_count': len(cls.__get_user_numbers(
                    lucky_user.id, activity_id)),
                'time': lucky_order.pay_at.split('.')[0]
            }
        }
        activity_win.announce_info = json.dumps(
            announce_info, ensure_ascii=False)
        activity_win.save(auto_commit=False)
        return announce_info['winner']

    @classmethod
    def __cache_winner(cls, activity_id, winner_info):
        redis_cache.set_activity_winner(
            activity_id, json.dumps(winner_info, ensure_ascii=False))
        redis_cache.add_user_winn(winner_info['uid'], activity_id)

    @classmethod
    def __award_order(cls, order_id):
        order = Order.query.filter(
            Order.id == order_id).with_lockmode('update').one()
        if order.status != ORDER_STATUS.PAYED:
            raise_with_traceback(DataError('award order status invalid'))
        order.status = ORDER_STATUS.AWARDED
        order.save(auto_commit=False)
        return order

    @classmethod
    def __sync_award(cls, order, activity):
        # sync to awarded order
        awarded_order = AwardedOrder()
        awarded_order.order_id = order.id
        awarded_order.user_id = order.buyer
        awarded_order.activity_id = activity.id
        awarded_order.activity_name = activity.name
        awarded_order.term_number = activity.term_number
        awarded_order.status = order.status
        awarded_order.extend = order.extend
        awarded_order.save(auto_commit=False)

    @classmethod
    def announce(cls, activity, lucky_number, result_a, lottery, a_list, order_id):
        try:
            cls.__announce_activity(activity, lucky_number)
            order = cls.__award_order(order_id)
            winner_info = cls.__announce_win(
                activity.id, lucky_number, order, result_a, lottery, a_list)
            cls.__cache_winner(activity.id, winner_info)
            cls.__sync_award(order, activity)
            cls.__update_user_activity_status(activity.id)
            orm.session.commit()
            _LOGGER.info('announce db success. activity id:%s, order_id:%s' %
                         (activity.id, order_id))
            return order
        except Exception as e:
            orm.session.rollback()
            raise_with_traceback(DbError(
                'announce db fail(%s). activity id:%s, order_id:%s',
                (e, activity.id, order_id)))
        finally:
            orm.session.close()
