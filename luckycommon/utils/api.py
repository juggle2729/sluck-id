# -*- coding: utf-8 -*-
import decimal
import json
import logging
import re
from datetime import datetime
from functools import wraps

import geoip2.database
from bson.objectid import ObjectId
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from future.utils import raise_with_traceback
from geoip import geolite2

from luckycommon.utils import exceptions as err
from luckycommon.utils.respcode import StatusCode

_LOGGER = logging.getLogger('lucky')

DEFAULT_COUNTRY = "OTHER"

city_reader = geoip2.database.Reader(settings.GEOLITE_CITY_DB)


def check_params(params, required_params, optional_param_dct=None):
    for param in required_params:
        if param not in params:
            raise_with_traceback(err.ParamError('missing %s' % param))

    if optional_param_dct:
        for param in optional_param_dct:
            if param not in params:
                # NOTE: we modified param by ref here
                params[param] = optional_param_dct[param]


def check_auth(req):
    if not req.user_id:
        raise err.AuthenticateError(status=StatusCode.INVALID_TOKEN)


# for class based view, use `method_decorator`
def token_required(func):
    @csrf_exempt
    @wraps(func)
    def _wrapped(req, *args, **kwargs):
        check_auth(req)
        return func(req, *args, **kwargs)

    return _wrapped


def get_country(ip, locale=None):
    country = ""
    geo = geolite2.lookup(ip)
    if geo:
        country = geo.country
    if not country and locale:
        try:
            lang, cty = re.split(r'[-_]', locale)
            country = cty
        except:
            pass
    return country or DEFAULT_COUNTRY


def get_city(ip, lan=settings.CITY_LAN):
    try:
        city_obj = city_reader.city(ip)
        return city_obj.city.names.get(lan)
    except:
        return None


def get_client_ip(request):
    ip = None
    real_ip = request.META.get('HTTP_X_REAL_IP')
    if real_ip:
        ip = real_ip.split(',')[0]
    if not ip or ip == "unknown":
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_ua(request):
    return request.META.get('HTTP_USER_AGENT', '')


class EnhencedEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        elif isinstance(o, datetime):
            return o.isoformat(' ')
        elif isinstance(o, ObjectId):
            return str(o)
        return super(EnhencedEncoder, self).default(o)


class JsonResponse(HttpResponse):
    """
        JSON response, since django 1.7, it's included in django.
    """

    def __init__(self, content, content_type='application/json; charset=utf-8',
                 **kwargs):
        super(JsonResponse, self).__init__(
            content=json.dumps(
                content, cls=EnhencedEncoder, ensure_ascii=False),
            content_type=content_type,
            **kwargs
        )


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def dict2obj(dct):
    s = Struct(**dct)

    return s


def parse_p(p):
    if not p:
        return {}
    l = p.split(',')
    m = [x.strip('[]') for x in l]
    d = dict((x.split(':')[0], x.split(':')[1]) for x in m)
    return d
