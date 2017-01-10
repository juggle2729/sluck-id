# -*- coding: utf-8 -*-
import json
import copy
import logging

from luckycommon.model import orm
from luckycommon.campaign.model.fortune_wheel import *
from luckycommon.credit.db.credit import add_credit_in_transaction
from luckycommon.db.coupon import award_coupon_in_transaction

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils import exceptions as err


_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def complete_task(user_id, date_str, task_index):
    add_times = TASK_CONF[task_index]['add_times']
    item = FortuneWheel.query.filter(FortuneWheel.user_id == user_id
        ).filter(FortuneWheel.date == date_str).with_lockmode('update').first()
    if not item:
        item = FortuneWheel()
        item.user_id = user_id
        item.date = date_str
        item.apply_times = 0
        left_times = DEFAULT_TIMES + add_times
        task_conf = copy.deepcopy(TASK_CONF)
    else:
        left_times = item.left_times + add_times
        task_conf = json.loads(item.task_status)
        if 1 == task_conf[task_index]['status']:
            return None

    if item.apply_times > MAX_TIMES or left_times > MAX_TIMES:
        _LOGGER.warn('fortune wheel apply times reached max, uid:%s', user_id)
        left_times = 0
    item.left_times = left_times
    for i, task in enumerate(task_conf):
        if i == task_index:
            task_conf[i]['status'] = 1
            break
    item.task_status = json.dumps(task_conf, ensure_ascii=False)
    item.save()
    return item


@sql_wrapper
def get_wheel(user_id, date_str):
    return FortuneWheel.query.filter(FortuneWheel.user_id == user_id
        ).filter(FortuneWheel.date == date_str).with_lockmode('update').first()


@sql_wrapper
def play_wheel(user_id, date_str, award_index):
    item = FortuneWheel.query.filter(FortuneWheel.user_id == user_id
        ).filter(FortuneWheel.date == date_str).with_lockmode('update').first()
    if not item:
        if DEFAULT_TIMES <= 0:
            raise err.ResourceInsufficient('reach limit', status=StatusCode.REACH_LIMIT)
        item = FortuneWheel()
        item.user_id = user_id
        item.date = date_str
        item.apply_times = 1
        item.left_times = DEFAULT_TIMES - 1
        item.task_status = json.dumps(TASK_CONF, ensure_ascii=False)
    elif item.left_times <= 0:
        raise err.ResourceInsufficient('reach limit', status=StatusCode.REACH_LIMIT)
    else:
        item.left_times -= 1
        item.apply_times += 1
    item.save(auto_commit=False)
    award_item = FortuneWheelAward()
    award_item.user_id = user_id
    award_item.date = date_str
    award_item.times_index = item.apply_times
    award_item.award_index = award_index
    award_item.status = AWARD_STATUS.WAIT_SHIP
    award_item.save(auto_commit=False)
    orm.session.commit()
    return award_item


@sql_wrapper
def fake_wheel(user_id, date_str, award_index):
    award_item = FortuneWheelAward()
    award_item.user_id = user_id
    award_item.date = date_str
    award_item.times_index = 1
    award_item.award_index = award_index
    award_item.status = AWARD_STATUS.WAIT_SHIP
    award_item.save()


@sql_wrapper
def award_deal(award_id):
    item = FortuneWheelAward.query.filter(
        FortuneWheelAward.id == award_id).filter(
        FortuneWheelAward.status == AWARD_STATUS.WAIT_SHIP).with_lockmode('update').one()
    user_id = item.user_id
    award_index = item.award_index
    if 0 == award_index:
        # 30 credit
        add_credit_in_transaction(user_id, 30, u'幸运抽奖元宝')
    if 1 == award_index:
        # 50 credit
        add_credit_in_transaction(user_id, 50, u'幸运抽奖元宝')
    if 2 == award_index:
        # 1 price coupon 
        award_coupon_in_transaction(user_id, 197)
    if 3 == award_index:
        # 10 price coupon 
        award_coupon_in_transaction(user_id, 198)
    item.status = AWARD_STATUS.DEAL
    item.save()


@sql_wrapper
def get_award_timeline():
    return FortuneWheelAward.query.order_by(FortuneWheelAward.created_at.desc()).limit(10).all()


@sql_wrapper
def get_user_award(user_id, limit=0, offset=0):
    query = FortuneWheelAward.query.filter(FortuneWheelAward.user_id == user_id)
    query = query.order_by(FortuneWheelAward.updated_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    return query.all()
