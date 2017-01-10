# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import json
import time
import random
import logging

from luckycommon.model import orm
from luckycommon.model.activity import ACTIVITY_STATUS, Activity, HotActivity

from luckycommon.cache import redis_cache
from luckycommon.utils import id_generator
from luckycommon.db.activity import create_user_activity, get_latest_term
from luckycommon.virtual.virtual_buy import buy_one


_LOGGER = logging.getLogger('worker')


def new_activity_index(activity, weight):
    _LOGGER.info('new_activity_index:%s %s %s' %
                (activity.id, activity.template_id, activity.term_number))
    # create hot activity index
    try:
        hot_activity = HotActivity()
        hot_activity.template_id = activity.template_id
        hot_activity.term_number = activity.term_number
        hot_activity.status = activity.status
        hot_activity.unit = activity.unit
        hot_activity.target_amount = activity.target_amount
        hot_activity.current_amount = activity.current_amount
        hot_activity.left_amount = activity.target_amount - activity.current_amount
        hot_activity.hot = weight
        hot_activity.save()
    except Exception as e:
        _LOGGER.error('create new activity index fail.%s' % e)
        orm.session.rollback()
    finally:
        orm.session.close()


def modify_template_hot(template_id, weight):
    _LOGGER.info('modify_template_hot:%s %s' % (template_id, weight))
    try:
        query = HotActivity.query.filter(HotActivity.template_id == template_id)
        query.update({'hot': weight})
        orm.session.commit()
    except Exception as e:
        _LOGGER.error('modify template hot fail.%s' % e)
        orm.session.rollback()
    finally:
        orm.session.close()


def modify_hot_activity(activity_id):
    _LOGGER.info('modify_hot_activity:%s' % activity_id)
    try:
        activity = Activity.query.filter(Activity.id == activity_id).one()
        pool_flag = redis_cache.check_numbers_pool(activity_id)
        if pool_flag:
            activity.current_amount = activity.target_amount - redis_cache.get_left_numbers_count(activity.id)
        else:
            activity.current_amount = redis_cache.get_lucky_numbers_count(activity.id)

        query = HotActivity.query
        query = query.filter(HotActivity.template_id == activity.template_id)
        query = query.filter(HotActivity.term_number == activity.term_number)
        hot_activity = query.one()

        if activity.status >= ACTIVITY_STATUS.ANNOUNCE_READY:
            hot_activity.delete()
        else:
            hot_activity.unit = activity.unit
            hot_activity.target_amount = activity.target_amount
            hot_activity.current_amount = activity.current_amount
            hot_activity.left_amount = activity.target_amount - activity.current_amount
            hot_activity.save()
    except Exception as e:
        _LOGGER.exception('modify_hot_activity %s, fail.(%s)' % (activity_id, e))
        orm.session.rollback()
        raise e
    finally:
        orm.session.close()


def index_user_activity(user_id, activity_id, numbers):
    _LOGGER.info('index_user_activity, %s %s' % (user_id, activity_id))
    create_user_activity(user_id, activity_id, numbers)


_DEFAULT_BUY_TIMES = 3
_TEMPLATE_LIST = [166,129,183,184,182,134,136,163,135,130,158,152,146,147]


def _choose_activity():
    template_id = random.choice(_TEMPLATE_LIST)
    latest_term = get_latest_term(template_id)
    activity_id = id_generator.generate_uuid(
        'activity:%s:%s' % (template_id, latest_term))
    return activity_id


def virtual_buy_random(target_id, times=_DEFAULT_BUY_TIMES):
    _LOGGER.info('virtual_buy_random for:%s' % target_id)
    count = 0
    while count < times:
        try:
            activity_id = _choose_activity()
            res = buy_one(activity_id)
            if res:
                data = json.loads(res).get('data')
                _LOGGER.info('virtual_buy_random %s:%s for %s', data.get('order_id'), data.get('order_numbers'), target_id)
                count += 1
                time.sleep(0.5)
            else:
                _LOGGER.error('virtual_buy_random fail for %s.', target_id)
        except Exception as e:
            _LOGGER.exception('virtual_buy_random exception, %s' % e)
        

if __name__ == "__main__":
    import sys
    activity_id = sys.argv[1]
    modify_hot_activity(activity_id)
