# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import json
import urllib
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model import orm
from luckycommon.model.account import *
from luckycommon.third.image import upload_data

cmd = sys.argv[1]
if cmd == 'update':
    agents = Account.query.filter(Account.is_virtual=1).all()
    for agent in agents:
        avatar_id = agent.avatar_id
        if avatar_id and '7xov75' not in avatar_id:
            r = urllib.urlopen(avatar_id)
            obj = r.read()
            data = base64.b64decode(img.read())
            url = upload_data(data, key_prefix='avatars')
            print 'fix %s %s to %s' % (agent.id, avatar_id, url)
            Account.query.filter(Account.id==agent.id).update({'avatar_id': url})
            orm.session.commit()
