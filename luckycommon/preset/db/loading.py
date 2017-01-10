# -*- coding: utf-8 -*-
import logging

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object, get, upsert, delete
from luckycommon.preset.model.loading import Loading

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_loading(id):
    return get(Loading, id)


@sql_wrapper
def upsert_loading(info, id=None):
    return upsert(Loading, info, id)


@sql_wrapper
def list_loading(query_dct):
    return list_object(query_dct, Loading)


@sql_wrapper
def delete_loading(id):
    delete(Loading, id)
