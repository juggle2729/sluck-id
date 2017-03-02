# -*- coding: utf-8 -*-
import json
import requests

url = 'https://www.googleapis.com/oauth2/v3/tokeninfo'


def get_user_profile(access_token):
    response = requests.get(url, {'id_token': access_token})
    json_data = json.loads(response.text)
    third_id = json_data['sub']
    username = json_data['name']
    avatar_url = json_data['picture']
    return third_id, username, avatar_url