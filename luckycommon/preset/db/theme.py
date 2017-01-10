# -*- coding: utf-8 -*-
import logging

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object, get, upsert, delete
from luckycommon.preset.model.theme import Theme

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_theme(id):
    return get(Theme, id)


@sql_wrapper
def upsert_theme(info, id=None):
    return upsert(Theme, info, id)


@sql_wrapper
def list_theme(query_dct):
    return list_object(query_dct, Theme)


@sql_wrapper
def delete_theme(id):
    delete(Theme, id)


@sql_wrapper
def clone_theme(theme_id):
    theme = Theme()
    base_inst = Theme.query.filter(Theme.id == theme_id).one().as_dict()
    for k in ('id', 'created_at', 'updated_at'):
        base_inst.pop(k, None)
    theme = theme.from_dict(base_inst)
    theme.save()
    return theme