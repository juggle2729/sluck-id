#! coding=utf-8
import sys, os

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.statistic.handle import Methodproxy, Merge, MailProxy
from luckycommon.model import orm
from luckycommon.cache import redis_cache
from decimal import Decimal
import datetime
from luckycommon.account.db.account import get_account_status
from luckycommon.model.activity import ActivityWin, UserActivity, Activity
from luckycommon.model.pay import Pay
from luckycommon.account.model.account import Account

today = (datetime.datetime.utcnow()-datetime.timedelta(days=1)).strftime('%Y-%m-%d')
start_time = '%s 00:00:00' % today
end_time = '%s 23:59:59' % today
start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')


def get_id_list():
    pay_info = orm.session.query(Pay.user_id).filter(Pay.status == 2, Pay.created_at >= start_time,
                                                     Pay.created_at <= end_time).all()
    pay_info_set = set(map(lambda x: x[0], pay_info))
    return list(pay_info_set)

def calc_column_value1(self, uid_list):
    info_list = orm.session.query(Account.phone).filter(Account.id.in_(uid_list)).all()
    def _convert_num(x):
        if not x[0]:
            return "000"
        return x[0]
    return map(lambda x: _convert_num(x), info_list)

def calc_column_value2(self, uid):
    pay_info = orm.session.query(Pay.price).filter(Pay.user_id == uid, Pay.status == 2,
                                                   Pay.created_at > "2017-02-01").all()
    def convert_func(value):
        if isinstance(value, Decimal):
            return int(value)
        else:
            return 0
    pay_value_list = map(lambda x: convert_func(x[0]), pay_info)
    if len(pay_value_list) > 1:
        return int(reduce(lambda x, y: x + y, pay_value_list))
    else:
        return int(pay_value_list[0])

def _get_borong_user(uid_list):
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
    def convert_dic_info(uid):
        return vip_borong_info_dic.get(uid, {"num":0, "amount":0}).values()[::-1]
    return map(lambda x: convert_dic_info(x), uid_list)


def calc_column_value3(self, uid_list):
    return map(lambda x: x[0], _get_borong_user(uid_list))


def calc_column_value4(self, uid_list):
    return map(lambda x: int(x[1]), _get_borong_user(uid_list))






column_method_1 = Methodproxy("test_column1")
column_method_1.close_iter()
column_method_1.inject_calc_value(calc_column_value1)

column_method_2 = Methodproxy("test_column2")
column_method_2.inject_calc_value(calc_column_value2)

column_method_3 = Methodproxy("test_column3")
column_method_3.close_iter()
column_method_3.inject_calc_value(calc_column_value3)

column_method_4 = Methodproxy("test_column4")
column_method_4.close_iter()
column_method_4.inject_calc_value(calc_column_value4)


# calculate result and save
merge_worker = Merge()
merge_worker.add_column_method_pool(column_method_1)
merge_worker.add_column_method_pool(column_method_2)
merge_worker.add_column_method_pool(column_method_3)
merge_worker.add_column_method_pool(column_method_4)
merge_worker.inject_id_list(id_list=get_id_list())
merge_worker.calculate_value()
merge_worker.merge_info(merge_worker.id_list, column_method_1.result_value, column_method_2.result_value)

mail_list = [
    'aaa@zhuohan-tech.com',
    'bbb@zhuohan-tech.com',
    'ccc@zhuohan-tech.com',
]

# mail sender
mail_proxy = MailProxy()
# mail_proxy.add_mail_to_list(mail_list)
mail_proxy.send_format_value_file(table_info = ["uid"]+[x.column_name for x in merge_worker.column_method_pool],
                                  value = merge_worker.table_value,
                                  file_name="daily_vip_user_info",
                                  mail_info="test statis report")
