# -*- coding: utf-8 -*-
import logging

from luckycommon.model.activity import *

from luckycommon.utils.decorator import sql_wrapper

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_tids_by_key(search_key):
    id_list = []
    templates = ActivityTemplate.query.filter(
        ActivityTemplate.name.like('%%%s%%' % search_key)).all()
    for template in templates:
        id_list.append(template.id)
    return id_list
