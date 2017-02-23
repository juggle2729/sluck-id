# -*- coding: utf-8 -*-
import json

import requests

from luckyplatform import settings


def collect_event(collection, properties, user_id=None):
    if user_id:
        properties['_user'] = user_id
    url = "http://54.179.142.74:9999/event/collect"
    headers = {
        'content-type': "application/json"
    }
    payload = {
        "collection": collection if not settings.DEBUG else collection + '_test',
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


if __name__ == '__main__':
    print collect_event('demo', {'click': False, '_user': 123})
