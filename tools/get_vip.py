# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.activity import ActivityWin, UserActivity, Activity
from luckycommon.model.pay import Pay
from luckycommon.account.model.account import Account
from luckycommon.cache import redis_cache
from luckycommon.account.db.account import get_account_status
from decimal import Decimal
from luckycommon.utils.mail import MailSender

mail_sender = MailSender.getInstance()
mail_sender.init_conf({
    'server':
    'smtp.mxhichina.com:25',
    'user':
    'ops@zhuohan-tech.com',
    'passwd':
    'madP@ssw0rd',
    'from':
    'Adsquare Service Statistics<ops@zhuohan-tech.com>',
    'to': [
        'zhulei@zhuohan-tech.com',
        'xialu@zhuohan-tech.com',
        'mahongli@zhuohan-tech.com',
        # 'liuyu@zhuohan-tech.com',
        'sstong@zhuohan-tech.com',
        'taocheng@zhuohan-tech.com',
        # 'chenweiran@zhuohan-tech.com',
        'lichang@zhuohan-tech.com',
        'xialu@zhuohan-tech.com',
        'caonianci@zhuohan-tech.com',
        # 'wywu@zhuohan-tech.com',
    ]
})

today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
html_str = u'<html><head></head><body><h2> VIP用户信息（%s）</h2>' % today
html_str += u'<table border="1"><tr><th>UID</th><th>Phone</th><th>总充值金额</th>' \
            u'<th>包场购买次数</th><th>包场中奖金额</th></tr>'


def _get_pay_count(user_id=None, pay_type=None):
    if user_id is None:
        return 0
    all_pays = Pay.query.filter(Pay.user_id == user_id).filter(
        Pay.status == 2).all()
    if pay_type is not None:
        all_pays.filter(Pay.pay_type == pay_type).all()
    all_amount = 0
    for pay in all_pays:
        if pay.price is not None:
            all_amount += pay.price
    return all_amount


def _borong_user(start_time, end_time):
    activity_win_query = ActivityWin.query.filter(
        ActivityWin.updated_at >=
        start_time.strftime('%Y-%m-%d %H:%M:%S')).filter(
            ActivityWin.updated_at <=
            end_time.strftime('%Y-%m-%d %H:%M:%S')).order_by(
                ActivityWin.updated_at.desc()).all()
    for item in activity_win_query:
        user_id = item.winner
        if redis_cache.is_virtual_account(user_id):  # 排除自有用户
            continue
        if get_account_status(user_id):  # 排除黑名单用户
            continue
        activity_id = item.activity_id
        user_activity = UserActivity.query.filter(
            UserActivity.user_id == user_id).filter(
                UserActivity.activity_id == activity_id).first()
        user_numbers = user_activity.numbers.split(',')
        activity = Activity.query.filter(Activity.id == activity_id).first()
        if not activity:
            continue
        if len(user_numbers) == activity.target_amount:
            redis_cache.add_borong_user(user_id)
            borong_info = redis_cache.get_borong_info(user_id)
            borong_num = borong_info.get('num', 0)
            borong_amount = borong_info.get('amount', 0)
            borong_num = int(borong_num) + 1
            borong_amount = Decimal(
                borong_amount) + activity.target_amount * activity.price
            redis_cache.set_borong_info(user_id, borong_num, borong_amount)


def _get_vip_user(size, offset, borong_users, borong_limit_num):
    global html_str
    if size > 1000:
        return
    accounts = Account.query.filter(Account.is_virtual == 0).filter(
        Account.status == 0).offset(offset).limit(size).all()

    for account in accounts:
        user_id = account.id
        a_all_amount = _get_pay_count(user_id=account.id)
        if a_all_amount >= 1000.00:
            if str(user_id) in borong_users:
                borong_info = redis_cache.get_borong_info(user_id)
                borong_num = borong_info.get('num', 0)
                borong_amount = borong_info.get('amount', 0)
                if int(borong_num) < borong_limit_num:
                    print str(user_id), account.phone, str(
                        a_all_amount), borong_num, str(borong_amount)
                    html_str += u'<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                        str(user_id), account.phone, str(a_all_amount),
                        borong_num, str(borong_amount))
            else:
                print str(user_id), account.phone, str(a_all_amount), 0, 0
                html_str += u'<tr><td>%s</td><td>%s</td><td>%s</td><td>0</td><td>0</td></tr>' % (
                    str(user_id), account.phone, str(a_all_amount))


if __name__ == '__main__':
    start_time = '%s 00:00:00' % today
    end_time = '%s 23:59:59' % today
    print today, start_time, end_time
    start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    _borong_user(start_time, end_time)
    print 'vip info'
    users = redis_cache.get_borong_user()
    SIZE = 100
    user_num = Account.query.count()
    loop_num = user_num / SIZE + 1
    for n in range(loop_num):
        offset = n * SIZE
        _get_vip_user(SIZE, offset, users, 5)
    html_str += u'</table></body></html>'
    mail_sender.send(u"%s -- VIP用户信息" % today, html_str)
    print 'end job.'
