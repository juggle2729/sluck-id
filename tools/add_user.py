# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.account.db import account as account_db
from luckycommon.model.virtual import VirtualPool

for i in xrange(5):
    phone = '1892323' + str(i)
    account = account_db.create_account({
        'nick_name': 'chaoge',
        'password': 123456,
        'avatar_id': '',
        'phone': phone,
        'email': '',
        'country': 'id',
        'is_virtual': 0
    }, 'channel_virtual', 'package_virtual')

    user, logon = account_db.login_account('phone', phone, 123456, extend=None)
    virtual_account = VirtualPool()
    virtual_account.user_id = user.id
    virtual_account.token = user.token
    virtual_account.save()
