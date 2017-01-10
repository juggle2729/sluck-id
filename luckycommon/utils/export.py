# -*- coding: utf-8 -*-
from os import path
from uuid import uuid4

import tablib
from django.conf import settings


def redirect_to_file(items, header, filename):
    file_path = path.join(settings.EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return {'url': '/export_data/%s' % filename}


def gen_filename(base):
    qs = base + '_' + str(uuid4())
    return qs + '.xlsx'
