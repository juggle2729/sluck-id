# -*- coding: utf-8 -*-
import json

import requests
from datetime import datetime

from luckyplatform import settings


def collect_event(collection, properties, user_id=None):
    if user_id:
        properties['_user'] = user_id
    if '_user' not in properties:
        properties['_user'] = ''
    url = settings.RAKAM_HOST + "/event/collect"
    headers = {
        'content-type': "application/json"
    }
    payload = {
        "collection": collection,
        "api": {
            "api_key": settings.MASTER_KEY,
            "library": {
                "name": "python",
                "version": "1.0"
            },
            "api_version": "1.0"
        },
        "properties": properties
    }
    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
    if response.text == '1':
        return True, None
    else:
        return False, response.text


def create_user(user_id, properties):
    url = settings.RAKAM_HOST + "/user/create"
    headers = {
        'content-type': 'application/json',
    }
    payload = {
        "id": user_id,
        "api": {
            "api_key": settings.WRITE_KEY,
            "library": {
                "name": "python",
                "version": "1.0"
            },
            "api_version": "1.0"
        },
        "properties": properties
    }
    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
    if response.text == '1':
        return True, None
    else:
        return False, response.text


def set_user_properties():
    pass


if __name__ == '__main__':
    # print collect_event('demo', {'click': False, '_user': 123})
    # print create_user(12345, {'is_virtual': '1', 'recharge': 30})
    print create_user(123253, {'is_virtual': False, 'channel': 'ofw', 'register_at': datetime.now()})
