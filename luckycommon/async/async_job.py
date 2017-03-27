# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import time
import random
import logging
import requests

from luckycommon.level.handler import add_exp
from luckycommon.model import orm
from luckycommon.model.virtual import VirtualPool
from luckycommon.model.activity import ACTIVITY_STATUS, Activity, HotActivity

from luckycommon.sunday.model.sunday import SUNDAY_TIDS
from luckycommon.sunday import callback as sunday_callback
from luckycommon.third.sms.helper import send_sms

from luckycommon.campaign import fortune_wheel, first_double, miss_return
from luckycommon.campaign import (daily_buy_campaign, recharge_campaign,
                                  new_recharge_campaign, moist_campaign)
from luckycommon.strategy import handler as strategy_handler
from luckycommon.partner import callback as partner_callback
from luckycommon.activity.auto_shipping import shipping_coin
from luckycommon.mission import fresh_mission

from luckycommon.cache import redis_cache
from luckycommon.track import collect_event, create_user, set_user_properties, increment_user_property
from luckycommon.utils import id_generator
from luckycommon.order.db.order import get_order
from luckycommon.db.pay import get_pay
from luckycommon.db import activity as activity_db
from luckycommon.db import partner as partner_db
from luckycommon.credit.db.credit import add_consume_credit
from luckycommon.third.sms.helper import send_sms
from luckycommon.async.celery import app

from django.conf import settings

_LOGGER = logging.getLogger('worker')


def is_campaign_activity(activity):
    template_id = activity.template_id
    # check sunday campaign
    if template_id in SUNDAY_TIDS:
        return True
    return False


@app.task(name='activity.create_index')
def new_activity_index(activity, weight):
    _LOGGER.info('new_activity_index:%s %s %s' %
                 (activity.id, activity.template_id, activity.term_number))
    # create hot activity index
    try:
        # 过滤掉部分活动商品
        if is_campaign_activity(activity):
            return
        hot_activity = HotActivity()
        hot_activity.template_id = activity.template_id
        hot_activity.term_number = activity.term_number
        hot_activity.status = activity.status
        hot_activity.unit = activity.unit
        hot_activity.target_amount = activity.target_amount
        hot_activity.current_amount = activity.current_amount
        hot_activity.left_amount = activity.target_amount - activity.current_amount
        hot_activity.hot = weight
        template = activity_db.get_template(activity.template_id)
        hot_activity.added_at = template.added_at
        hot_activity.save()
    except Exception as e:
        _LOGGER.error('create new activity index fail.%s' % e)
        orm.session.rollback()
    finally:
        orm.session.close()


@app.task(name='activity.modify_template_hot')
def modify_template_hot(template_id, weight):
    _LOGGER.info('modify_template_hot:%s %s' % (template_id, weight))
    try:
        query = HotActivity.query.filter(
            HotActivity.template_id == template_id)
        query.update({'hot': weight})
        orm.session.commit()
    except Exception as e:
        _LOGGER.error('modify template hot fail.%s' % e)
        orm.session.rollback()
    finally:
        orm.session.close()


@app.task(name='activity.modify_hot_activity')
def modify_hot_activity(activity_id):
    _LOGGER.info('modify_hot_activity:%s' % activity_id)
    try:
        activity = activity_db.get_activity(activity_id)
        left_amount = activity.target_amount - activity.current_amount
        query = HotActivity.query
        query = query.filter(HotActivity.template_id == activity.template_id)
        query = query.filter(HotActivity.term_number == activity.term_number)
        hot_activity = query.first()

        if hot_activity:
            if activity.status >= ACTIVITY_STATUS.ANNOUNCE_READY or not left_amount:
                _LOGGER.info('modify_hot_activity %s, status:%s, left_amount:%s',
                             activity_id, activity.status, left_amount)
                hot_activity.delete()
            else:
                hot_activity.unit = activity.unit
                hot_activity.target_amount = activity.target_amount
                hot_activity.current_amount = activity.current_amount
                hot_activity.left_amount = left_amount
                hot_activity.save()
    except Exception as e:
        _LOGGER.exception('modify_hot_activity %s, fail.(%s)' %
                          (activity_id, e))
        orm.session.rollback()
        raise e
    finally:
        orm.session.close()


@app.task(name='activity.index_user_activity')
def index_user_activity(user_id, activity_id, numbers):
    _LOGGER.info('index_user_activity, %s %s' % (user_id, activity_id))
    activity_db.create_user_activity(user_id, activity_id, numbers)


_DEFAULT_BUY_TIMES = 3


def _choose_activity():
    template_list = activity_db.get_cheap_template_ids()
    template_id = random.choice(template_list)
    latest_term = activity_db.get_latest_term(template_id)
    activity_id = id_generator.generate_uuid(
        'activity:%s:%s' % (template_id, latest_term))
    return activity_id


def buy(user_id, token, activity_id, quantity):
    headers = {
        'X-AUTH-USER': user_id,
        'X-AUTH-TOKEN': token
    }
    pay_load = {
        'buy_quantity': quantity
    }
    _BUY_API = settings.ROOT_URL + '/api/v2/activitys/%s/pay'
    api_path = _BUY_API % activity_id
    try:
        r = requests.post(api_path, data=pay_load, headers=headers)
        if r.status_code == 200:
            return r.text
        else:
            return None
    except Exception as e:
        _LOGGER.error('buy requests exceptions, %s' % e)
        return None


def choose_agent():
    agent_id = redis_cache.get_random_virtual_account()
    agent_account = VirtualPool.query.filter(
        VirtualPool.user_id == agent_id).first()
    return agent_account.user_id, agent_account.token


def buy_one(activity_id, quantity=1):
    user_id, token = choose_agent()
    res = buy(user_id, token, activity_id, quantity)
    return res


@app.task(name='activity.virtual_buy_random')
def virtual_buy_random(target_id, times=_DEFAULT_BUY_TIMES):
    _LOGGER.info('virtual_buy_random for:%s' % target_id)
    count = 0
    while count < times:
        try:
            activity_id = _choose_activity()
            activity = activity_db.get_activity(activity_id)
            res = buy_one(activity_id, activity.unit)
            if res:
                data = json.loads(res).get('data')
                _LOGGER.info('virtual_buy_random %s:%s for %s', data.get(
                    'order_id'), data.get('order_numbers'), target_id)
                time.sleep(0.5)
            else:
                _LOGGER.error('virtual_buy_random fail for %s.', target_id)
        except Exception as e:
            _LOGGER.exception('virtual_buy_random exception, %s' % e)
        count += 1


@app.task(name='campaign.stats_consume')
def stats_consume(user_id, total_amount, coupon_amount=0):
    _LOGGER.info('stats consume %s:%s,%s', user_id,
                 total_amount, coupon_amount)
    consume_amount = total_amount - coupon_amount
    if not redis_cache.is_virtual_account(user_id):
        if consume_amount > 0:
            try:
                add_consume_credit(user_id, consume_amount)
            except Exception as e:
                _LOGGER.exception('check_consume_credit exception:%s', e)
        strategy_handler.add_new_amount(user_id, total_amount)
        fortune_wheel.callback_task(user_id, 1)
        if total_amount == 0 and coupon_amount == 0:
            fortune_wheel.callback_task(user_id, 2)
    if consume_amount > 0:
        add_exp(user_id, consume_amount)


@app.task(name='campaign.stats_recharge')
def stats_recharge(pay_id):
    pay = get_pay(pay_id)
    user_id = pay.user_id
    price = int(pay.price)
    _LOGGER.info('stats recharge %s:%s,%s', pay_id, user_id, price)
    if price > 0:
        partner_callback.reward_inviters(user_id, price)
        fresh_mission.check_step_d(user_id)
        # first_double.recharge_callback(user_id, price)


@app.task(name='partner.create_relation')
def create_partner_relation(user_id, invite_list):
    partner_db.create_relation(user_id, invite_list)


@app.task(name='partner.send_authcode')
def send_authcode(phone, code, country):
    _LOGGER.info('async sending sms for phone %s, code: %s' % (phone, code))
    send_sms([phone], 'auth_code', {'code': code}, country=country)


@app.task(name='activity.stats_announce')
def stats_announce(activity_id, winner):
    """
    活动开奖异步任务
    """
    _LOGGER.info('stats announce for:%s, winner:%s', activity_id, winner)
    activity = activity_db.get_activity(activity_id)
    if settings.ADV_FLAG:
        # 自动发夺宝币
        shipping_coin(activity)
    fortune_wheel.callback_task(winner, 5)
    miss_return.announce_callback(activity, winner)


@app.task(name='utils.track_one')
def track_one(collection, properties, user_id=None):
    _LOGGER.info('track one event into collection: %s' % collection)
    status, error_message = collect_event(collection, properties, user_id)
    if not status:
        _LOGGER.info('track failed, collection: %s, properties: %s, reason: %s' % (collection, properties, error_message))


@app.task(name='utils.track_new_user')
def track_new_user(user_id, properties):
    _LOGGER.info('track one new user %s' % user_id)
    status, error_message = create_user(user_id, properties)
    if not status:
        _LOGGER.info('track failed, user_id: %s, properties: %s, reason: %s' % (user_id, properties, error_message))


@app.task(name='utils.set_user_properties')
def set_user(user_id, properties):
    _LOGGER.info('set user properties %s, %s' % (user_id, properties))
    status, error_message = set_user_properties(user_id, properties)
    if not status:
        _LOGGER.info('track failed, user_id: %s, properties: %s, reason: %s' % (user_id, properties, error_message))


@app.task(name='utils.increment_user_property')
def increment_user(user_id, property, value):
    _LOGGER.info('increment user property %s, %s, %s' % (user_id, property, value))
    status, error_message = increment_user_property(user_id, property, value)
    if not status:
        _LOGGER.info('track failed, user_id: %s, property: %s, reason: %s' % (user_id, property, error_message))


if __name__ == "__main__":
    import sys

    activity_id = sys.argv[1]
    modify_hot_activity(activity_id)
