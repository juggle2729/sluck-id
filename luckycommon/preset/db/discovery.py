# -*- coding: utf-8 -*-
import logging

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object, get, upsert, delete
from luckycommon.preset.model.discovery import Discovery

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_discovery(id):
    return get(Discovery, id)


@sql_wrapper
def upsert_discovery(info, id=None):
    return upsert(Discovery, info, id)


@sql_wrapper
def list_discovery(query_dct):
    return list_object(query_dct, Discovery)


@sql_wrapper
def delete_discovery(id):
    delete(Discovery, id)
