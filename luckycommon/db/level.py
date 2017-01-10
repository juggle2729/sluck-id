# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.model import orm
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.model.level import *
from luckycommon.db.coupon import award_coupon_in_transaction

from luckycommon.utils import exceptions as err

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_level(user_id):
    return Level.query.filter(Level.user_id == user_id).first()


@sql_wrapper
def create_level(user_id, dct):
    level = Level()
    level.user_id = user_id
    for key, value in dct.iteritems():
        setattr(level, key, value)
    level.save()
    return level


@sql_wrapper
def update_level_with_dict(user_id, dct):
    level = Level.query.filter(Level.user_id == user_id).with_lockmode('update').first()
    for key, value in dct.iteritems():
        setattr(level, key, value)
    level.save()
    return level


@sql_wrapper
def activate_coupon(user_id, level_num, level_coupon_config):
    level = Level.query.filter(Level.user_id == user_id).with_lockmode('update').first()
    if not level:
        raise err.ParamError('level no access')
    coupon_dict = json.loads(level.coupon_status) or {}
    if str(level_num) not in coupon_dict:
        raise err.ParamError('level no access')
    if int(coupon_dict[str(level_num)]) != LEVEL_COUPON_STATUS.CAN_ACTIVATE:
        raise err.ParamError('level no access')
    coupon_dict[str(level_num)] = LEVEL_COUPON_STATUS.ALREADY_ACTIVATED
    for d in level_coupon_config:
        coupon_tid = d['template_id']
        coupon_count = d['count']
        for _ in range(coupon_count):
            award_coupon_in_transaction(user_id, coupon_tid)
    level.coupon_status = json.dumps(coupon_dict)
    level.save()


@sql_wrapper
def update_week_exp_with_dict(user_id, year, week, dct):
    week_exp = WeekExp.query.filter(WeekExp.user_id == user_id). \
        filter(WeekExp.year == year). \
        filter(WeekExp.week_num == week). \
        with_lockmode('update').first()
    for key, value in dct.iteritems():
        setattr(week_exp, key, value)
    week_exp.save()
    return week_exp


@sql_wrapper
def get_top_level(count):
    query = Level.query.filter().order_by(Level.exp.desc()).limit(count)
    return query.all()


@sql_wrapper
def get_week_exp(user_id, year, week_num):
    return WeekExp.query.filter(WeekExp.user_id == user_id). \
        filter(WeekExp.year == year). \
        filter(WeekExp.week_num == week_num). \
        first()


@sql_wrapper
def create_week_exp(user_id, year, week_num):
    week_exp = WeekExp()
    week_exp.user_id = user_id
    week_exp.year = year
    week_exp.week_num = week_num
    week_exp.exp = 0
    week_exp.save()
    return week_exp


@sql_wrapper
def get_top_week_exp(year, week_num, count):
    query = WeekExp.query.filter(WeekExp.year == year). \
        filter(WeekExp.week_num == week_num). \
        order_by(WeekExp.exp.desc()).limit(count)
    return query.all()


@sql_wrapper
def get_distinct_years():
    return orm.session.query(WeekExp.year).order_by(WeekExp.year.desc()).distinct()


@sql_wrapper
def get_distinct_weeks(year):
    return orm.session.query(WeekExp.week_num).filter(WeekExp.year == year).order_by(WeekExp.week_num.desc()).distinct()

