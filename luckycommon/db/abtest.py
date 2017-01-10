# -*- coding: utf-8 -*-
import logging

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object, get, upsert, delete
from luckycommon.model.abtest import ABTest

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def list_abtest(query_dct):
    return list_object(query_dct, ABTest)


@sql_wrapper
def get_abtest(id):
    return get(ABTest, id)


@sql_wrapper
def upsert_abtest(info, id=None):
    return upsert(ABTest, info, id)


@sql_wrapper
def delete_abtest(id):
    delete(ABTest, id)
