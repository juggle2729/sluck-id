# -*- coding: utf-8 -*-
import json

import requests


def collect_event(collection, properties, user_id=None):
    if user_id:
        properties['_user'] = user_id
    if '_user' not in properties:
        properties['_user'] = ''
    url = "http://54.179.142.74:9999/event/collect"
    headers = {
        'content-type': "application/json"
    }
    payload = {
        "collection": collection,
        "api": {
            "api_key": "4cj10bvb4ptfi7jhbc39r90h6a69msflm2hiicroloftvbcbc8b0v56n2shhqo7a",
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
    url = "http://54.179.142.74:9999/user/create"
    headers = {
        'content-type': 'application/json',
    }
    payload = {
        "id": user_id,
        "api": {
            "api_key": "5svsjrik67tluh44s9000svfk21rlc073p1vrrs6pj2ttlf9s6lvivom37ihc7h4",
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
    print create_user(1234, {'is_virtual': '1'})
