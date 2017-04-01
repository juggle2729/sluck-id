# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import re
import sys
import json

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model import orm
from luckycommon.account.db.account import get_account
from luckycommon.model.activity import ActivityWin, UserActivity
from luckycommon.order.model.order import Order


def calc_result(orders):
    result_a = 0
    a_list = []
    for order in orders:
        pay_at = order.pay_at
        account = get_account(order.buyer, use_cache=True)
        datas = re.split(r'[:,.]', pay_at.split(' ')[1])
        int_str = ''.join(datas)
        result_a += int(int_str)
        a_list.append({
            'time': pay_at,
            'code': int_str,
            'name': account.nick_name or 'Unknown',
            'uid': order.buyer,
        })

    return result_a, a_list


def recovery_activity_wins():
    for page in range(1, 11):
        activity_wins = ActivityWin.query.order_by(ActivityWin.created_at).offset((page - 1) * 7030).limit(7030).all()
        print 'page: {0}, activity win count: {1}'.format(page, len(activity_wins))

        for win_item in activity_wins:
            try:
                json.loads(win_item.announce_info)
                print 'activity win {0} is ok'.format(win_item.activity_id)
            except Exception as e:
                print e
                activity_id, lucky_number, winner_id, order_id = (win_item.activity_id, win_item.lucky_number,
                                                                  win_item.winner, win_item.order_id)
                print 'activity win {0} loss data'.format(activity_id)
                lucky_user = get_account(winner_id, use_cache=True)
                lucky_order = Order.query.filter(Order.id == order_id).one()
                geo_info = {} if not lucky_order.extend else json.loads(lucky_order.extend)
                activity_orders = Order.query.filter(Order.activity_id == activity_id).all()
                result_a, a_list = calc_result(activity_orders)

                user_activity = UserActivity.query.filter(UserActivity.user_id == winner_id).filter(
                    UserActivity.activity_id == activity_id).first()
                if not user_activity or not user_activity.numbers:
                    num_count = 0
                else:
                    num_count = len(user_activity.numbers.split(','))
                announce_info = {
                    'result_a': result_a,
                    'a_list': a_list,
                    'result_b': 0,
                    'lottery_phase': '105052222',
                    'lottery_reference': None,
                    'winner': {
                        'uid': lucky_user.id,
                        'avatar': lucky_user.avatar_id,
                        'nick_name': lucky_user.nick_name,
                        'ip': geo_info.get('ip'),
                        'addr': geo_info.get('addr'),
                        'num_count': num_count,
                        'time': lucky_order.pay_at.split('.')[0],
                    }
                }
                win_item.announce_info = json.dumps(announce_info, ensure_ascii=False)
                win_item.save(auto_commit=False)
                break

        try:
            orm.session.commit()
        except Exception as e:
            orm.session.rollback()
            print 'db commit failed, %s' % e
        finally:
            orm.session.close()

if __name__ == "__main__":
    recovery_activity_wins()
