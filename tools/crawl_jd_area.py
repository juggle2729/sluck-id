# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import logging
from urllib import quote
import json

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import requests

from luckycommon.order.model.order import Area
from django.utils.encoding import smart_unicode


API_URL_LVL_1 = 'https://router.jd.com/api?method=biz.address.allProvinces.query&app_key=ec8e41c562e143fb8d9b2c1144d24cb5&access_token=0968dc327d3a46af80b37d01d93b72938&timestamp=%s&v=1.0&format=json&param_json={}'
API_URL_LVL_2 = 'https://router.jd.com/api?method=biz.address.citysByProvinceId.query&app_key=ec8e41c562e143fb8d9b2c1144d24cb5&access_token=0968dc327d3a46af80b37d01d93b72938&timestamp=%s&v=1.0&format=json&param_json={"id":%s}'
API_URL_LVL_3 = 'https://router.jd.com/api?method=biz.address.countysByCityId.query&app_key=ec8e41c562e143fb8d9b2c1144d24cb5&access_token=0968dc327d3a46af80b37d01d93b72938&timestamp=%s&v=1.0&format=json&param_json={"id":%s}'
API_URL_LVL_4 = 'https://router.jd.com/api?method=biz.address.townsByCountyId.query&app_key=ec8e41c562e143fb8d9b2c1144d24cb5&access_token=0968dc327d3a46af80b37d01d93b72938&timestamp=%s&v=1.0&format=json&param_json={"id":%s}'

ts = quote('2016-05-26 20:12:00')

def crawl(area_id=0, level=0, name=''):
    print area_id, level, name
    if level == 0:
        api_url = API_URL_LVL_1 % ts
    elif level == 1:
        print 11111
        api_url = API_URL_LVL_2 % (ts, area_id)
        print 2222 
    elif level == 2:
        api_url = API_URL_LVL_3 % (ts, area_id)
    elif level == 3:
        api_url = API_URL_LVL_4 % (ts, area_id)
    else:
        return
    try:
        r = requests.post(api_url)
        print r.text
        r_obj = json.loads(r.text)
        if level == 0:
            data = r_obj['biz_address_allProvinces_query_response']
        elif level == 1:
            data = r_obj['biz_address_citysByProvinceId_query_response']
        elif level == 2:
            data = r_obj['biz_address_countysByCityId_query_response']
        elif level == 3:
            data = r_obj['biz_address_townsByCountyId_query_response']
        result_code = data['resultCode']
        result = data['result']
        if result_code == '0000':
            for k, v in result.items():
                a_name = smart_unicode(k)
                a_id = int(v) 
                print u'add new area, %s %s' % (a_name, a_id)
                area = JdArea()
                area.id = a_id
                area.name = a_name
                area.full_name = name + a_name
                area.parent_id = area_id
                area.save()
                crawl(a_id, level+1, area.full_name)
    except Exception as e:
        print 'exception in crawl, %s' % e


if __name__ == "__main__":
    crawl()
