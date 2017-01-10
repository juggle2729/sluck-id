# -*- coding: utf-8 -*-
import logging

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object, get, upsert, delete
from luckycommon.preset.model.shortcut import Shortcut

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_shortcut(id):
    return get(Shortcut, id)


@sql_wrapper
def upsert_shortcut(info, id=None):
    return upsert(Shortcut, info, id)


@sql_wrapper
def list_shortcut(query_dct):
    return list_object(query_dct, Shortcut)


@sql_wrapper
def delete_shortcut(id):
    delete(Shortcut, id)
