# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

import time
import json
import random
import requests
from datetime import datetime

from luckycommon.cache import redis_cache

from luckycommon.db.activity import get_activity, get_activity_users 
from luckycommon.utils.weight import weight_sample

from django.conf import settings


_HOSTS = settings.ROOT_URL 

_CREATE_USER_API = _HOSTS + '/api/v1/user/'

account_list = []

def _load_account(file_path):
    fd = open(file_path, 'r')
    for line in fd:
        line = line.strip()
        data = line.split('\t')
        user_id, token, nick_name  = data
        account_list.append({
            'user_id': user_id,
            'token': token,
            'nick_name': nick_name,
        }) 
    for account in account_list:
        redis_cache.add_virtual_account(account['user_id'])


_load_account('/home/ubuntu/af-env/luckyservice/luckycommon/virtual/update_list')


def update_account():
    for account in account_list:
        print 'update account:%s' % account
        headers = {
            'X-AUTH-USER': account['user_id'],
            'X-AUTH-TOKEN': account['token']
        }
        pay_load = {
            'nick_name': account['nick_name'],
        }
        data = json.dumps(pay_load, ensure_ascii=False)
        print data
        r = requests.put(_CREATE_USER_API, data=data, headers=headers)
        print r.text


if __name__ == "__main__":
    update_account()
