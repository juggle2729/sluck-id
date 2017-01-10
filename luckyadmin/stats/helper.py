# -*- coding: utf-8 -*-
"""
    this module is used to parse the query string and generate search result
    from MongoDB.

    Please read docs in luckycommon/db/helper
"""

import json
import logging
from datetime import datetime, timedelta

import pymongo
from dateutil import parser
from luckycommon.utils.tz import local_to_utc

DEFAULT_SIZE = 20

_LOGGER = logging.getLogger(__name__)


def guess_type(k, convert_timezone=True):
    try:
        k = float(k)
    except ValueError:
        try:
            k = parser.parse(k)
            if convert_timezone:
                return local_to_utc(k).replace(tzinfo=None)
            else:
                return k
        except ValueError:
            return k

    return k


def _parse_filter(filter_dct, field=None):
    for k, v in filter_dct.iteritems():
        if k in ('$lt', '$lte', '$gt', '$gte', '$neq', '$eq'):
            if isinstance(v, basestring):
                filter_dct[k] = guess_type(v)
        elif k in ('$in', '$notin'):
            if k == '$notin':
                k = '$nin'
            filter_dct[k] = v
        elif k == '$or':
            filter_dct[k] = [_parse_filter(x) for x in v]
        elif k in ('$page', '$size'):
            filter_dct[k] = int(v)
        # TODO: add other operator...
        elif not k.startswith('$'):
            if k == '_':
                continue
            if isinstance(v, basestring):
                if not v.startswith('$'):
                    filter_dct[k] = guess_type(v)
            else:
                filter_dct[k] = _parse_filter(v, k)

    filter_dct.pop('_', None)
    return filter_dct


def parse_query_dct(query_dct, allow_keyword_without_dollor=False):
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

    return _parse_filter(query_dct)


def _apply_filter(k, op, v):
    if isinstance(v, basestring) and v.startswith('$'):
        if v == '$null':
            return {k: None}
        elif v == '$!null':
            return {k: {"$ne": None}}
        else:
            v = v[1:]
    if op in ('$lt', '$lte', '$gt', '$gte', '$neq', '$eq', '$in', '$nin'):
        return {k: {op: v}}
    elif op == '$like':
        return {k: {"$regex": v, '$options': 'i'}}
    elif op == '$notlike':
        return {k: {"$not": {"$regex": v, '$options': ''}}}
    elif isinstance(v, datetime):
        # we assume when one use date="2015-01-01", it means:
        #    date>"2015-01-01T00:00:00" and date<="2015-01-02T00:00:00"
        return {k: {"$gt": v, "$lte": v + timedelta(days=1)}}
    else:
        return {k: v}


def generate_filter(query_dct):
    filters = []
    for k, v in query_dct.iteritems():
        if k in ('$or', '$and'):
            nested_filter = []
            for d in v:
                nested_filter.append(generate_filter(d))
            filters.append({k: nested_filter})
        elif not k.startswith('$'):
            if not isinstance(v, dict):
                filters.append(_apply_filter(k, '', v))
            else:
                for op, vv in v.iteritems():
                    filters.append(_apply_filter(k, op, vv))
    if len(filters) == 1:
        return filters[0]
    elif len(filters) > 1:
        return {"$and": filters}
    else:
        return {}


def get_orderby(orderby):
    if orderby is not None:
        desc = False
        if orderby.startswith('-'):
            desc = True
            orderby = orderby[1:]
        return [orderby, pymongo.DESCENDING] if desc else [
            orderby, pymongo.ASCENDING]
    return None


def paginate(query, query_dct):
    limit = query_dct.get("$size", DEFAULT_SIZE)
    page = query_dct.get("$page", 1)

    if page <= 0:
        page = 1
    offset = (page - 1) * limit
    if offset:
        query = query.skip(offset)
    if limit > 0:
        # limit < 0 means no limit
        query = query.limit(limit)
    return query


def list_object(query_dct, session):
    query_dct = parse_query_dct(query_dct)
    query = session.find(generate_filter(query_dct))
    total_count = query.count()
    orderby = get_orderby(query_dct.get('$orderby'))
    if orderby is not None:
        query = query.sort(*orderby)

    query = paginate(query, query_dct)

    return query, total_count
