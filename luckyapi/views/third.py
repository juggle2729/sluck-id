# -*- coding: utf-8 -*-
import json
import hashlib
import logging
import requests

from django.views.decorators.http import require_GET, require_POST
from django.conf import settings

from luckycommon.third.image import get_token, delete_data_by_key

from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import DataError, ParamError

_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
@token_required
def get_qiniu_token(req):
    bucket_name = settings.USER_BUCKET_NAME
    token = get_token(bucket_name, expires=3600)
    return {"token": token, "host": settings.QINIU_DOMAIN,
            "bucket": bucket_name}


@require_POST
@response_wrapper
@token_required
def delete_data(req):
    query_dct = json.loads(req.body)
    bucket_name = settings.USER_BUCKET_NAME
    keys = query_dct.get('keys', [])
    assert isinstance(keys, list)
    if keys:
        delete_data_by_key(keys, bucket_name)

    return {}

@require_GET
@response_wrapper
def datacell_f(req):
    _LOGGER.error('It seems Datacell Fail, %s', req.body)
    return {}


@response_wrapper
def datacell_s(req):
    _LOGGER.error('It seems Datacell , %s', req.body)
    return {}


@require_GET
@response_wrapper
def bluepay(req):
    _LOGGER.error('It seems Bluepay, %s', req.GET)
    return {'status':200}
