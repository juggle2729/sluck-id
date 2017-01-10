# -*- coding: utf-8 -*-
"""
    this module is used to parse the query string and generate search result
    from MySQL. Since we have wrote it before, this time something simpler.

    Agreement:
        Query string is always included in the url.
        keyword all start with '$', just like in mongodb.
        url format:

        /api/v1/resource1,resource2/?field1={"$lt": 1, "$gte": "$field3"}
            &field2=100&...&$orderby=field4&$page=3

        For desc order, use `-field4`.
        For datetime, use ISO format like '%Y-%m-%dT%H:%M:%S.%fZ'.
        For text search, use regex or simple glob(in mysql), keyword is
            '$like', '$notlike'.
        For `or`, use `$or`:
            /api/v1/resource1/?$or=[{field1: x}]

        (for compatibility reason, we allow 'page', 'limit',
        'orderby' with out '$'.)

        Group aggregate is too complex. even use mongo format, it is too hard
        to implement it in one page. So, just leave it here. Maybe you can
        write a parser or DSL here :)
"""

import json
import logging

from sqlalchemy import or_ as OR
from sqlalchemy import and_ as AND
from datetime import datetime, timedelta

from luckycommon.utils.orm import convert_type, get_count

DEFAULT_SIZE = 20

_LOGGER = logging.getLogger(__name__)


def _parse_filter(filter_dct, table, field=None):
    illegal = []
    for k, v in filter_dct.iteritems():
        if k in ('$lt', '$lte', '$gt', '$gte', '$neq', '$eq'):
            if isinstance(v, basestring) and not v.startswith('$'):
                filter_dct[k] = convert_type(table, field, v)
        elif k in ('$in', '$notin'):
            filter_dct[k] = [convert_type(table, field, x) for x in v]
        elif k == '$or':
            filter_dct[k] = [_parse_filter(x, table) for x in v]
        elif k in ('$page', '$size'):
            filter_dct[k] = int(v)
        # TODO: add other operator...
        elif not k.startswith('$'):
            if not hasattr(table, k):
                illegal.append(k)
                if k != '_':
                    _LOGGER.warn(
                        "%s not exist in table %s", k, table.__tablename__)
                continue
            if isinstance(v, basestring):
                if not v.startswith('$'):
                    filter_dct[k] = convert_type(table, k, v)
            else:
                filter_dct[k] = _parse_filter(v, table, k)

    for i in illegal:
        filter_dct.pop(i)
    return filter_dct


def parse_query_dct(query_dct, table, allow_keyword_without_dollor=False):
    """ preprocess from req.GET.dict(), return parsed query_dct.
    """
    for k, v in query_dct.iteritems():
        if v.startswith('{') or v.startswith('['):
            try:
                query_dct[k] = json.loads(v)
            except (ValueError, TypeError):
                continue

        if allow_keyword_without_dollor:
            if k in ('page', 'size', 'orderby'):
                if k in query_dct:
                    query_dct['$' + k] = query_dct[k]

    return _parse_filter(query_dct, table)


def _apply_filter(k, op, v, t):
    if isinstance(v, basestring) and v.startswith('$'):
        if v == '$null':
            return getattr(t, k) == None
        elif v == '$!null':
            return getattr(t, k) != None
        else:
            v = getattr(t, v[1:])
    if op == '$lt':
        return getattr(t, k) < v
    elif op == '$lte':
        return getattr(t, k) <= v
    elif op == '$gt':
        return getattr(t, k) > v
    elif op == '$gte':
        return getattr(t, k) >= v
    elif op == '$neq':
        return getattr(t, k) != v
    elif op == '$eq':
        return _apply_filter(k, '', v, t)
    elif op in ('$in', '$notin'):
        return getattr(getattr(t, k), op[1:] + '_')(v)
    elif op in ('$like', '$notlike'):
        return getattr(getattr(t, k), op[1:])("%%%s%%" % v)
    elif isinstance(v, datetime):
        # we assume when one use date="2015-01-01", it means:
        #    date>"2015-01-01T00:00:00" and date<="2015-01-02T00:00:00"
        return ((getattr(t, k) > v) &
                (getattr(t, k) <= v + timedelta(days=1)))
    else:
        return getattr(t, k) == v


def generate_filter(query_dct, table):
    filters = []
    for k, v in query_dct.iteritems():
        if k in ('$or', '$and'):
            nested_filter = []
            for d in v:
                nested_filter.append(generate_filter(d, table))
            OP = OR if k == '$or' else AND
            filters.append(OP(*nested_filter))
        elif not k.startswith('$'):
            if not isinstance(v, dict):
                filters.append(_apply_filter(k, '', v, table))
            else:
                for op, vv in v.iteritems():
                    filters.append(_apply_filter(k, op, vv, table))
    return filters[0] if len(filters) == 1 else AND(*filters)


def get_orderby(orderby, table):
    if orderby is not None:
        desc = False
        if orderby.startswith('-'):
            desc = True
            orderby = orderby[1:]
        if not hasattr(table, orderby):
            return None
        return getattr(table, orderby).desc() if desc else getattr(
            table, orderby)
    return None


def paginate(query, query_dct):
    limit = query_dct.get("$size", DEFAULT_SIZE)
    page = query_dct.get("$page", 1)

    if limit > 0:
        # limit < 0 means no limit
        query = query.limit(limit)
    if page <= 0:
        page = 1
    offset = (page - 1) * limit
    query = query.offset(offset)
    return query


def list_object(query_dct, table):
    query_dct = parse_query_dct(query_dct, table)
    query = table.query.filter(generate_filter(query_dct, table))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), table)
    if orderby is not None:
        query = query.order_by(orderby)

    query = paginate(query, query_dct)

    return query.all(), total_count


def get(table, id):
    return table.query.filter(table.id == id).first()


def upsert(table, data_dct, id=None):
    t = None
    if id:
        t = table.query.with_for_update().filter(
            table.id == id).first()
    if not t:
        t = table()
    for k, v in data_dct.iteritems():
        if hasattr(t, k) and k not in ('created_at', 'updated_at'):
            setattr(t, k, v)
    t.updated_at = datetime.utcnow()
    t.save()
    return t


def delete(table, id):
    t = table.query.with_for_update().filter(
        table.id == id).first()
    if t:
        t.delete()
