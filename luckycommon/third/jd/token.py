# -*- coding: utf-8 -*-
import logging
import requests
import json
from hashlib import md5

from future.utils import raise_with_traceback

from luckycommon.cache.redis_cache import get_jd_token, set_jd_token
from luckycommon.utils.exceptions import ServerError
from luckycommon.utils.tz import local_now

APP_KEY = "ec8e41c562e143fb8d9b2c1144d24cb5"
APP_SECRET = "0028d3b7cc4c4ba084f6501502e7bf7d"
USERNAME = u"VOP卓翰网络"
PASSWORD = "WHzh@7floor"
TOKEN_URL = "https://kploauth.jd.com/oauth/token"

_LOGGER = logging.getLogger(__name__)


def get_token(force_refresh=False):
    if not force_refresh:
        token = get_jd_token()
        if token:
            return token
    params = {
        "grant_type": "password",
        "app_key": APP_KEY,
        "app_secret": APP_SECRET,
        "state": 0,
        "username": USERNAME,
        "password": md5(PASSWORD).hexdigest()
    }
    resp = requests.get(TOKEN_URL, params)
    if not resp.ok:
        raise_with_traceback(ServerError(
            "can't get jd token for :%s" % resp.text))
    resp = json.loads(resp.content)
    set_jd_token(resp['access_token'], int(resp['expires_in'] * 0.9))
    return resp['access_token']

API_BASE = "https://router.jd.com/api"


def send_request(method, param_json=None):
    param_json = json.dumps(param_json or {})
    params = {
        'method': method,
        'app_key': APP_KEY,
        'app_secret': APP_SECRET,
        'access_token': get_token(),
        'timestamp': local_now().strftime('%Y-%m-%d %H:%M:%S'),
        'v': '1.0',
        'param_json': param_json
    }
    resp = requests.get(API_BASE, params)
    if not resp.ok:
        raise_with_traceback(ServerError(
            "request to jd server error: %s" % resp.text))
    resp = resp.json()
    if 'errorResponse' in resp:
        raise_with_traceback(ServerError(
            "request to jd error: %s" % resp))

    return resp
