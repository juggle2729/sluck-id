# -*- coding: utf-8 -*-
from __future__ import absolute_import

import uuid

import os
import sys
import json
import urllib
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'


fd = open('./alist', 'r')

for line in fd:
    line = line.strip()
    name = str(uuid.uuid4()) + '.jpeg'
    r = urllib.urlopen(line)
    obj = r.read()
    ft = open('./avatars/'+name, 'wb')
    ft.write(obj)
