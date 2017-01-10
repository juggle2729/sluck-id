# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime

from sqlalchemy import or_

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import (delete, get_orderby,
                                   parse_query_dct, paginate,
                                   generate_filter, get_count)
from luckycommon.preset.model.preset import Preset
from luckycommon.utils.api import EnhencedEncoder

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def get_preset(id=None, app_version=None, device_type=None):
    query = Preset.query
    if id:
        return query.filter(Preset.id == id).first()
    if app_version is not None:
        query = query.filter(
            # if not the default...
            Preset.min_version <= app_version).filter(
            or_(Preset.max_version >= app_version,
                Preset.max_version == None))
    if device_type is not None:
        query = query.filter(
            Preset.device_type.op('&')(device_type) > 0)
    inst = query.first()
    return inst if inst is not None else Preset.query.first()


@sql_wrapper
def upsert_preset(info=None, id=None, base=None):
    if id is not None:
        preset = Preset.query.with_for_update().filter(
            Preset.id == id).first()
    else:
        if base is not None:
            preset = Preset()
            base_inst = Preset.query.filter(Preset.id == base).one().as_dict()
            for k in 'id', 'created_at', 'updated_at':
                base_inst.pop(k, None)
            base_inst['last_modified'] = 0
            preset = preset.from_dict(base_inst)
        else:
            preset = Preset()
            preset.min_version = 1
            preset.max_version = None
            preset.device_type = 0
            preset.content = json.dumps({
                'scrolling': {},
                'banner': [],
                'pages': [],
                'shortcut': [],
                'discovery': [],
            })
            preset.last_modified = 0

        preset.created_at = preset.updated_at = datetime.utcnow()

    preset.last_modified += 1
    if info is not None:
        for k, v in info.iteritems():
            if hasattr(Preset, k) and k not in (
                    'last_modified', 'created_at', 'updated_at'):
                if k == 'content':
                    setattr(preset, k, json.dumps(
                        v, cls=EnhencedEncoder, ensure_ascii=False))
                else:
                    setattr(preset, k, v)
    preset.save()
    return preset


def list_preset(query_dct):
    version = query_dct.pop('version', None)
    device_type = query_dct.pop('device_type', None)

    if version:
        return [get_preset(app_version=int(version),
                           device_type=int(device_type))], 1

    query = Preset.query
    if device_type is not None:
        device_type = int(device_type)
        query = query.filter(Preset.device_type.op('&')(device_type) > 0)
    query = query.filter(generate_filter(
        parse_query_dct(query_dct, Preset), Preset))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), Preset)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)
    return query.all(), total_count


@sql_wrapper
def delete_preset(id):
    delete(Preset, id)
