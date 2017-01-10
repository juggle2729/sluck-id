# -*- coding: utf-8 -*-
import logging

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object, get, upsert, delete
from luckycommon.preset.model.banner import Banner

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_banner(id):
    return get(Banner, id)


@sql_wrapper
def upsert_banner(info, id=None):
    return upsert(Banner, info, id)


@sql_wrapper
def list_banner(query_dct):
    return list_object(query_dct, Banner)


@sql_wrapper
def delete_banner(id):
    delete(Banner, id)
