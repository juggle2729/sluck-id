# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import datetime
import tablib

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model import orm
from luckycommon.model.activity import ActivityWin, UserActivity, Activity
from luckycommon.model.pay import Pay
from luckycommon.account.model.account import Account
from luckycommon.cache import redis_cache
from luckycommon.account.db.account import get_account_status
from decimal import Decimal
from luckycommon.utils.mail import MailSender

today = (datetime.datetime.utcnow()-datetime.timedelta(days=1)).strftime('%Y-%m-%d')
start_time = '%s 00:00:00' % today
end_time = '%s 23:59:59' % today
start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')


def _get_user_charge_set():
    pay_info = orm.session.query(Pay.user_id).filter(Pay.status==2, Pay.created_at >=start_time, Pay.created_at<=end_time).all()
    pay_info_set = set(map(lambda x: x[0], pay_info))
    return list(pay_info_set)

def _get_phone_info(uid_list):
    info_list = orm.session.query(Account.phone).filter(Account.id.in_(uid_list)).all()
    def _convert_num(x):
        if not x[0]:
            return "000"
        return x[0]
    return map(lambda x: _convert_num(x), info_list)


def _get_all_pay_amount(uid=0):
    pay_info = orm.session.query(Pay.price).filter(Pay.user_id==uid, Pay.status==2, Pay.created_at>"2017-02-01").all()
    def convert_func(value):
        if isinstance(value, Decimal):
            return int(value)
        else:
            return 0
    pay_value_list = map(lambda x: convert_func(x[0]), pay_info)
    if len(pay_value_list)>1:
        return int(reduce(lambda x,y: x+y, pay_value_list))
    else:
        return int(pay_value_list[0])


def _get_daily_pay_amount(uid=0):
    pay_info = orm.session.query(Pay.price).filter(Pay.user_id==uid, Pay.status==2, Pay.created_at>=start_time, Pay.created_at<=end_time).all()
    def convert_func(value):
        if isinstance(value, Decimal):
            return int(value)
        else:
            return 0
    pay_value_list = map(lambda x: convert_func(x[0]), pay_info)
    if len(pay_value_list)>1:
        return int(reduce(lambda x,y: x+y, pay_value_list))
    else:
        return int(pay_value_list[0])


def _get_borong_user():
    vip_borong_info_dic = {}
    activity_win_query = orm.session.query(ActivityWin.winner, ActivityWin.activity_id).filter(
        ActivityWin.updated_at >=
        start_time).filter(
        ActivityWin.updated_at <=
        end_time).all()
    for item in activity_win_query:
        user_id = item[0]
        if redis_cache.is_virtual_account(user_id):  # 排除自有用户
            continue
        if get_account_status(user_id):  # 排除黑名单用户
            continue
        activity_id = item[1]
        user_activity = orm.session.query(UserActivity.numbers).filter(
            UserActivity.user_id == user_id).filter(
            UserActivity.activity_id == activity_id).first()
        user_numbers = user_activity[0].split(',')
        activity = Activity.query.filter(Activity.id == activity_id).first()
        if not activity:
            continue
        if len(user_numbers) == activity.target_amount:
            borong_info = vip_borong_info_dic.get(user_id, {})
            borong_num = borong_info.get('num', 0)
            borong_amount = borong_info.get('amount', 0)
            borong_num = int(borong_num) + 1
            borong_amount = Decimal(
                borong_amount) + activity.target_amount * activity.price
            vip_borong_info_dic[user_id] = {"num": borong_num, "amount": borong_amount}
    return vip_borong_info_dic


TOOL_MAIL_SENDER = MailSender.getInstance()
TOOL_MAIL_SENDER.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@zhuohan-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@zhuohan-tech.com>',
    'to': [
        'yzhen@zhuohan-tech.com',
    ]
})


EXPORT_PATH = "/home/ubuntu/af-env/data/"

def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path


if __name__ == '__main__':
    ###
    #1: get statistic target instance id_list
    #2: use decleared function to get value list in id_list order for every columns
    #3: zip all the value list into a big result list
    ###
    # get id_list
    uid_list = _get_user_charge_set()
    # get value_list

    phone_info_list = _get_phone_info(uid_list)
    user_charge_value_list = map(lambda x: _get_all_pay_amount(uid=x), uid_list)
    user_daliy_charge_value_list = map(lambda x: _get_daily_pay_amount(uid=x), uid_list)
    borong_info_dic = _get_borong_user()
    def convert_dic_info(uid):
        return borong_info_dic.get(uid, {"num":0, "amount":0}).values()[::-1]
    borong_info_list = map(lambda x: convert_dic_info(x), uid_list)
    borong_times_info = map(lambda x: x[0], borong_info_list)
    borong_amount_info = map(lambda x: int(x[1]), borong_info_list)
    # zip all the value_list
    info_list = zip(uid_list, phone_info_list, user_charge_value_list, borong_times_info, borong_amount_info)
    result_info_list = []
    for i in info_list:
        if i[2] > 500:
            result_info_list.append(i)
    table_title = ["uid", "phone", "today_pay_amount", "all_pay_amount", "bor_time", "bor_amount"]
    file_path = redirect_to_file(result_info_list, table_title, u'daily_pay_user%s.xlsx' % end_time.strftime('%y-%m-%d %HH:%MM:%S'))
    TOOL_MAIL_SENDER.send(u"%s--VIP用户信息"%today, "to see the attachment", attachments=[file_path])


