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
from luckycommon.model.activity import Activity, UserActivity
from luckycommon.model.account import Account
from luckycommon.utils.mail import MailSender
from luckycommon.utils.tz import utc_to_local_str

from django.conf import settings


mail_sender = MailSender.getInstance()
mail_sender.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@adsquare-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@adsquare-tech.com>',
    # 'to': ['shuxiang@adsquare-tech.com'],
    'to': ['liuyu@adsquare-tech.com',
           'dongtongjing@adsquare-tech.com',
           'wangshanshan@adsquare-tech.com',
           'wangfeng@adsquare-tech.com',
           'shuxiang@adsquare-tech.com']
})

virtual_set = redis_cache.get_virtual_account()

a_dict = {}
now_d = datetime.utcnow().replace(hour=16, minute=0, second=0)
start_d = now_d - timedelta(days=7)
start_str = start_d.strftime('%Y-%m-%d %H:%M:%S')
end_str = now_d.strftime('%Y-%m-%d %H:%M:%S')
user_activitys = UserActivity.query.filter(UserActivity.created_at > start_str)\
                                   .filter(UserActivity.created_at < end_str).all()
for ua in user_activitys:
    activity_id = ua.activity_id
    user_id = ua.user_id
    if str(user_id) in virtual_set: 
        continue
    activity = Activity.query.filter(Activity.id == activity_id).first()
    template_id = activity.template_id
    name = activity.name
    key = '%s-%s' % (template_id, name)
    a_dict.setdefault(key, {'uids': set(), 'amount': 0})
    a_dict[key]['uids'].add(user_id)
    a_dict[key]['amount'] += len(ua.numbers.split(','))
    # print 'add %s to %s' % (user_id, template_id)

b_dict = [{'id':k,'count':len(v['uids']),'amount':v['amount']} for k,v in a_dict.items()]
b_dict.sort(key=lambda x: x['count'], reverse=True)
html_str = '<html><head></head><body>'
html_str += u'<table border="1"><tr><td>商品编号</td><td>购买人次</td><td>购买金额</td></tr>'
for item in b_dict:
    html_str += u'<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (item['id'], item['count'], item['amount'])
html_str += '</table>'
html_str += '</body></html>'
#print html_str
mail_sender.send(u"上周商品排名", html_str)
