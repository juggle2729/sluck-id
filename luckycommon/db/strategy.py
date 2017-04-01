# -*- coding: utf-8 -*-
import json
import logging
import datetime
import pytz

from luckycommon.model import orm
from luckycommon.model.strategy import *
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.tz import utc_to_local


_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_current_amount(daily_limit):
    today = utc_to_local(datetime.datetime.now(pytz.UTC))
    today_str = today.strftime('%Y-%m-%d')
    _LOGGER.info('#strategy# today_str: %s, today: %s' % (today_str, today))
    query = DailyAmount.query.filter(DailyAmount.date == today_str)
    item = query.first()
    if not item:
        # create
        yesterday = today - datetime.timedelta(days=1)
        yesterday_amount = DailyAmount.query.filter(
            DailyAmount.date == yesterday.strftime('%Y-%m-%d')).first()
        if not yesterday_amount:
            left_amount = 0
            left_manual_amount = 0
        else:
            left_amount = yesterday_amount.amount_limit - \
                yesterday_amount.current_amount
            left_manual_amount = yesterday_amount.manual_amount_limit - \
                yesterday_amount.manual_amount
        item = DailyAmount()
        item.date = today_str
        item.current_amount = 0
        item.manual_amount = 0
        item.current_count = 0
        # check default daily limit
        config_item = StrategyConfig.query.first()
        if not config_item:
            default_daily_limit = daily_limit
            default_manual_daily_limit = daily_limit
        else:
            default_daily_limit = config_item.amount_limit
            default_manual_daily_limit = config_item.manual_amount_limit
        if left_amount > 0:
            item.amount_limit = default_daily_limit + left_amount
        else:
            item.amount_limit = default_daily_limit
        if left_manual_amount > 0:
            item.manual_amount_limit = default_manual_daily_limit + \
                left_manual_amount
        else:
            item.manual_amount_limit = default_manual_daily_limit
        item.save()
    return item


@sql_wrapper
def add_current_amount(add_amount, winner_id, manual_intervention=False):
    try:
        today = utc_to_local(datetime.datetime.now())
        today_str = today.strftime('%Y-%m-%d')
        item = DailyAmount.query.filter(DailyAmount.date == today_str).first()
        extend = {} if not item.extend else json.loads(item.extend)
        if manual_intervention:
            item.manual_amount += add_amount
            extend.setdefault('loser', [])
            extend['loser'].append(winner_id)
        else:
            item.current_amount += add_amount
            extend.setdefault('winner', [])
            extend['winner'].append(winner_id)
        item.extend = json.dumps(extend, ensure_ascii=False)
        item.current_count += 1
        item.save()
    except Exception as e:
        _LOGGER.exception('add_current_amount exception, %s', e)


@sql_wrapper
def set_current_limit(amount_limit=None, manual_amount_limit=None):
    today = utc_to_local(datetime.datetime.now())
    today_str = today.strftime('%Y-%m-%d')
    item = DailyAmount.query.filter(DailyAmount.date == today_str).first()
    if amount_limit:
        item.amount_limit = amount_limit
    if manual_amount_limit:
        item.manual_amount_limit = manual_amount_limit
    item.save()


@sql_wrapper
def set_strategy_config(amount_limit=None, manual_amount_limit=None):
    config_item = StrategyConfig.query.first()
    if not config_item:
        config_item = StrategyConfig()
    if amount_limit:
        config_item.amount_limit = amount_limit
    if manual_amount_limit:
        config_item.manual_amount_limit = manual_amount_limit
    config_item.save()


@sql_wrapper
def get_strategy_config():
    return StrategyConfig.query.first()


LEVEL_LIST = [
    {
        'level': 1,
        'exp': 20,
        'privilege_type_list': [PRIVILEGE_TYPE.TYPE_A]
    },{
        'level': 2,
        'exp': 100,
        'privilege_type_list': [PRIVILEGE_TYPE.TYPE_B]
    },{
        'level': 3,
        'exp': 500,
        'privilege_type_list': [PRIVILEGE_TYPE.TYPE_C, PRIVILEGE_TYPE.TYPE_A]
    },{
        'level': 4,
        'exp': 1000,
        'privilege_type_list': [PRIVILEGE_TYPE.TYPE_D, PRIVILEGE_TYPE.TYPE_A, PRIVILEGE_TYPE.TYPE_B]
    },{
        'level': 5,
        'exp': 2000,
        'privilege_type_list': [PRIVILEGE_TYPE.TYPE_E, PRIVILEGE_TYPE.TYPE_B] + [PRIVILEGE_TYPE.TYPE_A]*2
    },{
        'level': 6,
        'exp': 4000,
        'privilege_type_list': [PRIVILEGE_TYPE.TYPE_F] + [PRIVILEGE_TYPE.TYPE_A]*3 + [PRIVILEGE_TYPE.TYPE_B]*2
    },{
        'level': 7,
        'exp': 10000,
        'privilege_type_list': [PRIVILEGE_TYPE.TYPE_G, PRIVILEGE_TYPE.TYPE_C] + [PRIVILEGE_TYPE.TYPE_A]*3 + [PRIVILEGE_TYPE.TYPE_B]*2
    }
]


@sql_wrapper
def adjust_privilege_level(user_id, latest_exp):
    query = StrategyAchievement.query.filter(StrategyAchievement.user_id == user_id)
    item = query.order_by(StrategyAchievement.level.desc()).first()
    max_level = 0 if not item else item.level
    for level_info in LEVEL_LIST:
        if level_info['level'] <= max_level:
            continue
        if latest_exp >= level_info['exp']:
            # upgrade
            new_level = level_info['level']
            _LOGGER.info('%s reached new level %s', user_id, new_level)
            level_item = StrategyAchievement()
            level_item.user_id = user_id
            level_item.level = new_level
            level_item.exp = latest_exp
            # get privilege
            p_list = []
            privilege_type_list = level_info['privilege_type_list']
            for privilege_type in privilege_type_list: 
                privilege_item = StrategyPrivilege()
                privilege_item.user_id = user_id
                privilege_item.privilege_type = privilege_type
                privilege_item.save(auto_commit=False)
                orm.session.flush()
                p_list.append(str(privilege_item.id))
                _LOGGER.info('%s got privilege %s', user_id, privilege_type)
            level_item.privileges = ','.join(p_list)
            level_item.save()


@sql_wrapper
def add_special_privilege(user_id):
    privilege_item = StrategyPrivilege()
    privilege_item.user_id = user_id
    privilege_item.privilege_type = 0
    privilege_item.save()


@sql_wrapper
def get_privilege_users(target_amount):
    items = []
    match_type = StrategyPrivilege.calc_privilege_type(target_amount)
    if 1 == match_type:
        # 检查A+特权, 返回特权相关的限制数据
        items = StrategyPrivilege.query.filter(StrategyPrivilege.privilege_type == 0)\
                                       .filter(StrategyPrivilege.used == 0).all()
        if items:
            match_type = 0
    if not items:
        items = StrategyPrivilege.query.filter(StrategyPrivilege.privilege_type == match_type)\
                                       .filter(StrategyPrivilege.used == 0).all()
    uids = set()
    for item in items:
        uids.add(item.user_id)
    return uids, PRIVILEGE_CONF[match_type]


@sql_wrapper
def get_user_privileges(user_id):
    items = StrategyPrivilege.query.filter(StrategyPrivilege.user_id == user_id)\
                                   .filter(StrategyPrivilege.used == 0).all()
    return items


@sql_wrapper
def consume_privilege(user_id, activity):
    try:
        target_privilege = None
        match_type = StrategyPrivilege.calc_privilege_type(activity.target_amount)
        if match_type == 1:
            target_privilege = StrategyPrivilege.query.filter(StrategyPrivilege.privilege_type == 0)\
                                                      .filter(StrategyPrivilege.user_id == user_id)\
                                                      .filter(StrategyPrivilege.used == 0).first()
        if not target_privilege:
            target_privilege = StrategyPrivilege.query.filter(StrategyPrivilege.privilege_type == match_type)\
                                                      .filter(StrategyPrivilege.user_id == user_id)\
                                                      .filter(StrategyPrivilege.used == 0).first()
        target_privilege.used = 1
        target_privilege.activity_id = activity.id
        target_privilege.save()
    except Exception as e:
        _LOGGER.exception('consume privilege exception, %s', e)
