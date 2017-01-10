# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
from datetime import timedelta
from datetime import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache  import redis_cache
from luckycommon.model.activity import ActivityTemplate, Activity, UserActivity, ActivityWin
from luckycommon.model.stock import Goods
from luckycommon.account.model.account import Account
from luckycommon.model.category import Category, CategoryActivity
from luckycommon.utils.mail import MailSender
from luckycommon.utils.tz import utc_to_local_str

from django.conf import settings


mail_sender = MailSender.getInstance()
mail_sender.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@zhuohan-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@zhuohan-tech.com>',
    'to': [
        'zhulei@zhuohan-tech.com',
        'mahongli@zhuohan-tech.com',
        'liuyu@zhuohan-tech.com',
#        'sstong@zhuohan-tech.com',
        'renxiaoyu@zhuohan-tech.com',
        'wjxiao@zhuohan-tech.com',
    ]
})

virtual_set = redis_cache.get_virtual_account()

now_d = datetime.utcnow().replace(hour=16, minute=0, second=0)
start_d = now_d - timedelta(days=7)
start_str = start_d.strftime('%Y-%m-%d %H:%M:%S')
end_str = now_d.strftime('%Y-%m-%d %H:%M:%S')

a_dict = {}
win_set = set()

user_activitys = UserActivity.query.filter(UserActivity.created_at > start_str)\
                                   .filter(UserActivity.created_at < end_str).all()
template_ids = set()
for ua in user_activitys:
    user_id = ua.user_id
    activity_id = ua.activity_id
    activity = Activity.query.filter(Activity.id == activity_id).first()
    template_id = activity.template_id
    template_ids.add(template_id)
    a_dict.setdefault(template_id, {
        'uids': set(),
        'vids': set(),
        'virtual_amount': 0,
        'real_amount': 0,
        'real_win': 0,
        'virtual_win': 0,
    })
    if activity_id not in win_set:
        activity_win = ActivityWin.query.filter(ActivityWin.activity_id == activity_id).first()
        if activity_win:
            winner_id = activity_win.winner
            if str(winner_id) not in virtual_set:
                a_dict[template_id]['real_win'] += 1
            else:
                a_dict[template_id]['virtual_win'] += 1
        win_set.add(activity_id)
    if str(user_id) in virtual_set:
        a_dict[template_id]['vids'].add(user_id)
        a_dict[template_id]['virtual_amount'] += len(ua.numbers.split(','))
    else:
        a_dict[template_id]['uids'].add(user_id)
        a_dict[template_id]['real_amount'] += len(ua.numbers.split(','))

template_list = ActivityTemplate.query.filter(ActivityTemplate.id.in_(template_ids)).all()
for template in template_list:
    goods_id = template.goods_id
    goods = Goods.query.filter(Goods.id == goods_id).first()
    goods_price = goods.price
    activity_name = template.name
    activity_price = template.target_amount
    category_template = CategoryActivity.query.filter(CategoryActivity.template_id == template.id).first()
    if category_template:
        category_id = category_template.category_id
        category = Category.query.filter(Category.id == category_id).first()
        category_name = category.name
    else:
        category_name = u'暂无分类'
    a_dict[template.id]['name'] = template.name
    a_dict[template.id]['category'] = category_name
    a_dict[template.id]['goods_price'] = goods_price
    a_dict[template.id]['activity_price'] = activity_price


b_dict = [{
    'id':k,
    'name':v['name'],
    'category':v['category'],
    'goods_price':v['goods_price'],
    'activity_price':v['activity_price'],
    'real_person':len(v['uids']),
    'virtual_person':len(v['vids']),
    'real_amount':v['real_amount'],
    'virtual_amount':v['virtual_amount'],
    'real_win':v['real_win'],
    'virtual_win':v['virtual_win'],
} for k,v in a_dict.items()]
b_dict.sort(key=lambda x: x['goods_price'], reverse=True)
html_str = '<html><head></head><body>'
html_str += u'''<table border="1"><tr><td>商品编号</td>
                                      <td>商品名称</td>
                                      <td>商品分类</td>
                                      <td>商品成本</td>
                                      <td>活动价格</td>
                                      <td>渠道用户购买人数</td>
                                      <td>自有用户购买人数</td>
                                      <td>渠道用户购买金额</td>
                                      <td>自有用户购买金额</td>
                                      <td>渠道用户中奖次数</td>
                                      <td>自有用户中奖次数</td>
</tr>'''
for item in b_dict:
    html_str += u'<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (item['id'], item['name'], item['category'], item['goods_price'], item['activity_price'], item['real_person'], item['virtual_person'],
item['real_amount'], item['virtual_amount'], item['real_win'], item['virtual_win'])
html_str += '</table>'
html_str += '</body></html>'

mail_sender.send(u"上周商品排名", html_str)
