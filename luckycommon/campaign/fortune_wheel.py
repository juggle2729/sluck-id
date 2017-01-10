# -*- coding: utf-8 -*-
import json
import random
import logging
from datetime import datetime

from luckycommon.campaign.model.fortune_wheel import *
from luckycommon.campaign.db import fortune_wheel as wheel_db

from luckycommon.cache import redis_cache
from luckycommon.account.db.account import get_account

from luckycommon.utils import id_generator
from luckycommon.utils.tz import local_now, utc_to_local
from luckycommon.utils import exceptions as err

from django.conf import settings


_LOGGER = logging.getLogger('lucky')


def _choose_award():
    rand_int = random.randint(1, 100)
    index = 0
    for ratio_item in AWARD_RATIO:
        if rand_int >= ratio_item['start'] and rand_int <= ratio_item['end']:
            return index
        index += 1
    return 0


def fake_wheel():
    date_str = local_now().strftime('%Y-%m-%d')
    rand_int = random.randint(1, 100)
    if rand_int <= 0:
        award_index = 5 # iphone
        agent_id = redis_cache.get_random_virtual_account()
        wheel_db.fake_wheel(agent_id, date_str, award_index)
        _LOGGER.info('fortuen wheel fake, %s awarded %s',
            agent_id, award_index)
    elif rand_int < 10:
        award_index = 4 # 50元话费
        agent_id = redis_cache.get_random_virtual_account()
        wheel_db.fake_wheel(agent_id, date_str, award_index)
        _LOGGER.info('fortuen wheel fake, %s awarded %s',
            agent_id, award_index)


def single_play(user_id):
    """
    转一次
    """
    date_str = local_now().strftime('%Y-%m-%d')
    award_index = _choose_award()
    award_item = wheel_db.play_wheel(user_id, date_str, award_index)
    # 目前全是虚拟商品，自动发货
    wheel_db.award_deal(award_item.id)
    _LOGGER.info('fortuen wheel, %s awarded %s in %s times',
        user_id, award_index, award_item.times_index)
    # fake wheel
    try:
        fake_wheel()
    except:
        pass
    return award_index


def get_status(user_id):
    """
    获取当天参与情况，包括任务完成情况和参与次数
    """
    data = {}
    date_str = local_now().strftime('%Y-%m-%d')
    item = wheel_db.get_wheel(user_id, date_str)
    if not item:
        data.update({
            'left_times': DEFAULT_TIMES,
            'apply_times': 0,
            'task_status': TASK_CONF
        })
    else:
        task_status = json.loads(item.task_status)
        data.update({
            'left_times': item.left_times,
            'apply_times': item.apply_times,
            'task_status': task_status
        })
    return data


def get_timeline():
    a_list = []
    items = wheel_db.get_award_timeline()
    for item in items:
        award_name = AWARD_RATIO[item.award_index]['name']
        user_id = item.user_id
        account = get_account(user_id)
        a_list.append({
            'user_id': user_id,
            'nick_name': account.nick_name,
            'award_index': item.award_index,
            'award_name': award_name
        })
    return a_list


_DEFAULT_PAGE_SIZE = 20


def get_user_award(user_id, page, size):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    a_list = []
    items = wheel_db.get_user_award(user_id, limit, offset)
    for item in items:
        award_name = AWARD_RATIO[item.award_index]['name']
        a_list.append({
            'award_time': utc_to_local(item.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'award_index': item.award_index,
            'award_name': award_name,
            'status': item.status
        })
    return a_list


def callback_task(user_id, task_index):
    """
    每日任务完成回调
    """
    try:
        date_str = local_now().strftime('%Y-%m-%d')
        item = wheel_db.complete_task(user_id, date_str, task_index)
        if item:
            _LOGGER.info('fortune wheel, %s complete task %s, left %s times',
            user_id, task_index, item.left_times)
    except Exception as e:
        _LOGGER.exception('fortuen wheel, callback_task exception:%s', e)
