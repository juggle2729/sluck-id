# -*- coding: utf-8 -*-
import sys
import os
import requests

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "luckyplatform.settings")

from luckycommon.cache.redis_cache import set_wechat_token, check_wechat_ttl
from luckyplatform.settings import WX_APP_ID, WX_SECRET_KEY

MIN_TTL = 30 * 60       # cron run every 10 mins
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"

ttl = check_wechat_ttl()
if ttl <= MIN_TTL:
    resp = requests.get(TOKEN_URL, {
        'grant_type': 'client_credential',
        'appid': WX_APP_ID,
        'secret': WX_SECRET_KEY
    })
    if resp.ok:
        resp = resp.json()
        if resp.get('errmsg'):
            print resp
        else:
            set_wechat_token(resp['access_token'], resp['expires_in'])
    else:
        print resp.text
