# coding=utf-8
import logging

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object, get, upsert, delete
from luckycommon.preset.model.homepage import Homepage

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_homepage(id):
    return get(Homepage, id)


@sql_wrapper
def upsert_homepage(info, id=None):
    return upsert(Homepage, info, id)


@sql_wrapper
def list_homepage(query_dct):
    return list_object(query_dct, Homepage)


@sql_wrapper
def delete_homepage(id):
    delete(Homepage, id)