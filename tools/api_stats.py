# -*- coding:utf-8 -*-
import os
import re
import sys
from datetime import datetime, timedelta

from luckycommon.utils.mail import TOOL_MAIL_SENDER

#223.104.25.78 - - [07/Jul/2016:17:49:59 +0800]  "GET /api/v2/my/activitys?page=2 HTTP/1.1" 200 7515 "http://www.1yuan-gou.com/user/my_activity_record" "Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.53" 0.183 0.183 .

NGINX_COM=re.compile('(\d+\.\d+\.\d+\.\d+) - - \[(.*)\]  "(.*?) (.*?) HTTP/1.1" (\d+) (\d+) "(.*?)" "(.*?)" (.*?) (.*?) \.')
NAME_PATHS = [
    re.compile(r'^/api/v1/receipts/(?P<receipt_id>[^/]+)/modify/?$'),
    re.compile(r'^/api/v1/receipts/(?P<receipt_id>[^/]+)/remove/?$'),
    re.compile(r'^/api/v1/activitys/(?P<activity_id>[^/]+)/?$'),
    re.compile(r'^/api/v1/groups/(?P<template_id>[^/]+)/terms/(?P<term_number>[^/]+)/?$'),
    re.compile(r'^/api/v1/groups/(?P<template_id>[^/]+)/winners/?$'),
    re.compile(r'^/api/v1/activitys/(?P<activity_id>[^/]+)/records/timeline/?$'),
    re.compile(r'^/api/v1/activitys/(?P<activity_id>[^/]+)/records/(?P<record_id>[^/]+)/?$'),
    re.compile(r'^/api/v1/activitys/(?P<activity_id>[^/]+)/records/?$'),
    re.compile(r'^/api/v1/activitys/(?P<activity_id>[^/]+)/calclist/?$'),
    re.compile(r'^/api/v1/activitys/(?P<activity_id>[^/]+)/billboard/?$'),
    re.compile(r'^/api/v1/pay/(?P<pay_id>[^/]+)/submit/?$'),
    re.compile(r'^/api/v1/pay/(?P<pay_id>[^/]+)/status/?$'),
    re.compile(r'^/api/v1/activitys/(?P<activity_id>[^/]+)/orders/(?P<order_id>[^/]+)/status/?$'),
    re.compile(r'^/api/v1/orders/(?P<order_id>[^/]+)/award/?$'),
    re.compile(r'^/api/v1/orders/(?P<order_id>[^/]+)/deal/?$'),
    re.compile(r'^/api/v1/orders/(?P<order_id>[^/]+)/?$'),
    re.compile(r'^/api/v1/activitys/(?P<activity_id>[^/]+)/pay/?$'),
    re.compile(r'^/api/v1/user/(?P<user_id>[^/]+)/shows/?$'),
    re.compile(r'^/api/v1/shows/(?P<show_id>[^/]+)/edit/?$'),
    re.compile(r'^/api/v1/shows/(?P<show_id>[^/]+)/?$'),
    re.compile(r'^/api/v1/coupons/(?P<group_coupon_id>[^/]+)/snatch/?$'),
    re.compile(r'^/api/v1/campaign/(?P<campaign_id>[^/]+)/achievement/?$'),
    re.compile(r'^/api/v1/campaign/(?P<campaign_id>[^/]+)/level/(?P<level_id>[^/]+)/activate/?$'),
    re.compile(r'^/api/v1/campaign/(?P<campaign_name>[^/]+)/recommend/?$'),
    re.compile(r'^/api/v1/campaign/(?P<campaign_name>[^/]+)/recommend/coupon/?$'),
    re.compile(r'^/api/v1/campaign/(?P<campaign_name>[^/]+)/recommend/award/?$'),
    re.compile(r'^/api/v1/campaign/(?P<campaign_name>[^/]+)/recommend/timeline/?$'),
    re.compile(r'^/api/v1/campaign/(?P<campaign_id>[^/]+)/timeline/?$'),
    re.compile(r'^/api/v1/categorys/(?P<category_id>[^/]+)/?$'),
    re.compile(r'^/api/v2/activitys/(?P<activity_id>[^/]+)/pay/?$'),
    re.compile(r'^/api/v2/user/(?P<user_id>[^/]+)/activitys/?$'),
    re.compile(r'^/api/v2/activitys/(?P<activity_id>[^/]+)/?$'),
    re.compile(r'^/api/v2/activitys/(?P<activity_id>[^/]+)/revealed?$'),
    re.compile(r'^/api/v2/groups/(?P<template_id>[^/]+)/winners/?$'),
    re.compile(r'^/api/v2/groups/(?P<template_id>[^/]+)/latest/?$'),
]
api_dict = dict()

sick_fd = open('./sick_api', 'w')

fd = open('/var/log/nginx/luckyshopweb.access.log.1','r')
for line in fd:
    line = line.strip()
    match = NGINX_COM.match(line)
    if match:
        client_ip = match.group(1)
        request_time = match.group(2)
        api_method = match.group(3)
        api_path = match.group(4)
        http_status = match.group(5)
        http_size = match.group(6)
        api_path = api_path.split('?')[0]
        if not api_path.startswith('/api/v'):
            continue
        for api_re in NAME_PATHS:  
            api_g = api_re.match(api_path)
            if api_g:
                api_path = api_re.pattern 
                break
        api_dict.setdefault(api_path, {
            'count': 0,
            'total_time': 0,
            'max_time': 0,
            'min_time': 0,
            'sick_count': 0, # >10s
            'bad_count': 0, # >1s & <10s
            '200_count': 0,
            '500_count': 0,
            '502_count': 0,
            '504_count': 0,
        })
        api_dict[api_path]['count'] += 1
        if http_status == '200' and api_method != 'OPTIONS':
            try:
                request_time = float(match.group(9))
                upstream_time = float(match.group(10))
                api_dict[api_path]['200_count'] += 1
                api_dict[api_path]['total_time'] += upstream_time
                if upstream_time > api_dict[api_path]['max_time']:
                    api_dict[api_path]['max_time'] = upstream_time
                if api_dict[api_path]['min_time'] == 0 or upstream_time < api_dict[api_path]['min_time']:
                    api_dict[api_path]['min_time'] = upstream_time
                if upstream_time >= 10:
                    api_dict[api_path]['sick_count'] += 1
                    sick_fd.write('%s\n' % line)
                if upstream_time >= 1 and upstream_time <= 10:
                    api_dict[api_path]['bad_count'] += 1
                    sick_fd.write('%s\n' % line)
            except:
                pass
        if http_status == '500':
            api_dict[api_path]['500_count'] += 1
        if http_status == '502':
            api_dict[api_path]['502_count'] += 1
        if http_status == '504':
            api_dict[api_path]['504_count'] += 1

# sort
api_list = [(k,v) for k,v in api_dict.items()]
api_list.sort(key=lambda x: x[1].get('count'), reverse=True)

html_str = '<html><head></head><body>'
html_str += u'<h1>API列表</h1><br />'
html_str += u'''<table border="1"><tr><td>API</td>
                                      <td>request times</td>
                                      <td>200 times</td>
                                      <td>500 times</td>
                                      <td>502 times</td>
                                      <td>504 times</td>
                                      <td>sick count</td>
                                      <td>bad count</td>
                                      <td>max consuming</td>
                                      <td>min consuming</td>
                                      <td>average consuming</td>
</tr>'''
for item in api_list:
    api_path = item[0]
    info = item[1]
    if info['200_count'] > 0:
        average_consuming = info['total_time'] / info['200_count']
    else:
        average_consuming = 0
    html_str += u'<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (api_path,
        info['count'], info['200_count'], info['500_count'], info['502_count'],
        info['504_count'], info['sick_count'], info['bad_count'], info['max_time'], info['min_time'], average_consuming)

html_str += '</table>'
html_str += '</body></html>'
#print html_str
d = datetime.now() - timedelta(1)
TOOL_MAIL_SENDER.send("[%s]API stats" % d.strftime('%Y-%m-%d'), html_str)
