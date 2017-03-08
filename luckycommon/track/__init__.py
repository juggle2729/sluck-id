# -*- coding: utf-8 -*-
import json

import requests

from django.conf import settings


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


def set_user_properties(user_id, properties):
    url = settings.RAKAM_HOST + "/user/set_properties"
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


def increment_user_property(user_id, property, value):
    url = settings.RAKAM_HOST + "/user/increment_property"
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
        "property": property,
        "value": value
    }
    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
    if response.text == '1':
        return True, None
    else:
        return False, response.text


if __name__ == '__main__':
    import os
    import sys
    sys.path.append('/home/ubuntu/af-env/luckyservice')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

    from luckycommon.account.model.account import Account
    for account in Account.query.filter().all():
        extend = json.loads(account.extend)
        create_user(account.id, {
            'balance': account.balance,
            'register_at': account.created_at.isoformat(),
            'channel': extend.get('chn'),
            'is_virtual': True if account.is_virtual else False,
        })
