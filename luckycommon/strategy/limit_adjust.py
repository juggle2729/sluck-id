import datetime
import logging
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.db.strategy import set_current_limit
from luckycommon.model.strategy import DailyAmount, StrategyConfig
from luckycommon.utils.tz import utc_to_local
from luckycommon.third.sms.helper import send_sms

_LOGGER = logging.getLogger('worker')

NOTIFY_PHONES = ['15927067926', '18674066001']


def sms_notify(left_normal_amount, left_manual_amount):
    try:
        params = {
            "normal_amount": left_normal_amount,
            "manual_amount": left_manual_amount,
        }
        send_sms(NOTIFY_PHONES, 'sms_strategy_amount', params)
        _LOGGER.info('sms notify strategy amount, %s-%s', left_normal_amount, left_manual_amount)
    except Exception as e:
        _LOGGER.exception('sms notify strategy amount exception, %s', e)


def check_current_limit():
    today = utc_to_local(datetime.datetime.now())
    today_str = today.strftime('%Y-%m-%d')
    query = DailyAmount.query.filter(DailyAmount.date == today_str)
    item = query.first()
    if item:
        amount_limit = item.amount_limit
        current_amount = item.current_amount
        manual_amount_limit = item.manual_amount_limit
        manual_amount = item.manual_amount
        _LOGGER.info('current strategy amount, normal amount:%s, normal limit:%s, manual amount:%s, manual limit:%s',
                     current_amount, amount_limit, manual_amount, manual_amount_limit)
        left_normal_amount = amount_limit - current_amount
        left_manual_amount = manual_amount_limit - manual_amount
        if left_normal_amount < 3000 or left_manual_amount < 3000:
            sms_notify(left_normal_amount, left_manual_amount)
    return item


def add_limit():
    current_item = check_current_limit()
    if current_item:
        config = StrategyConfig.query.first()
        add_amount = config.amount_limit / 3
        new_limit = current_item.amount_limit + add_amount
        new_manual_limit = current_item.manual_amount_limit
        set_current_limit(new_limit, new_manual_limit)
        _LOGGER.info('add daily amount %s, current_limit:%s, current_manual_limit:%s',
                     add_amount, new_limit, new_manual_limit)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'check':
        check_current_limit()
    if cmd == 'add':
        add_limit()
