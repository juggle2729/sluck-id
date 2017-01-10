# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

# add up one level dir into sys path
sys.path.append(
    os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.virtual import handler
from luckycommon.model.virtual import VirtualPool

from django.conf import settings


def import_virtual_pool(file_path=settings.LIST_UPDATE):
    account_list = []
    fd = open(file_path, 'r')
    for line in fd:
        line = line.strip()
        data = line.split('\t')
        if len(data) == 4:
            user_id, token, phone, nick_name  = data
            avatar = ''
        else:
            user_id, token, phone, nick_name, avatar  = data
        account_list.append({
            'user_id': user_id,
            'token': token,
            'phone': phone,
            'nick_name': nick_name,
            'avatar': avatar,
        }) 
    return account_list

if __name__ == "__main__":
    handler.create()
    #account_list = import_virtual_pool()
    #for account in account_list:
    #    virtual_pool = VirtualPool()
    #    virtual_pool.user_id = account['user_id']
    #    virtual_pool.token = account['token']
    #    virtual_pool.save()
