import requests
import json

_UID = None
_TOKEN = None
_HEADERS = {}


def test_login():
    payload = {'phone': '13971125425', 'password': '333333'}
    r = requests.post('http://192.168.0.72/api/v1/user/login', data=json.dumps(payload))
    data = json.loads(r.text).get('data')
    assert r.status_code == 200
    assert 'id' in data
    assert 'token' in data
    global _UID, _TOKEN, _HEADERS
    _UID = data['id']
    _TOKEN = data['token']
    _HEADERS = {
        'X-AUTH-USER': _UID,
        'X-AUTH-TOKEN': _TOKEN
    }


def test_get_user_info():
    r = requests.get('http://192.168.0.72/api/v1/user', headers=_HEADERS)
    data = json.loads(r.text).get('data')
    assert r.status_code == 200
    assert 'id' in data
    assert 'phone' in data
    assert 'level' in data


def test_get_auth_code():
    r = requests.get('http://192.168.0.72/api/v1/user/auth_code', headers=_HEADERS)
    data = json.loads(r.text).get('data')


def test_get_public_profile():
    r = requests.get('http://192.168.0.72/api/v1/user/public_profile', headers=_HEADERS)
    data = json.loads(r.text).get('data')


def test_get_receipts():
    r = requests.get('http://192.168.0.72/api/v1/receipts', headers=_HEADERS)
    data = json.loads(r.text).get('data')


def test_add_receipts():
    r = requests.post('http://192.168.0.72/api/v1/receipts/add', headers=_HEADERS)
    data = json.loads(r.text).get('data')


def test_modify_receipts():
    r = requests.post('http://192.168.0.72/api/v1/receipts//modify', headers=_HEADERS)
    data = json.loads(r.text).get('data')


def test_remove_receipts():
    r = requests.post('http://192.168.0.72/api/v1/receipts//remove', headers=_HEADERS)
    data = json.loads(r.text).get('data')


def test_create_template():
    r = requests.post('http://192.168.0.72/api/v1/create_template', headers=_HEADERS)
    data = json.loads(r.text).get('data')


def test_start_template():
    r = requests.post('http://192.168.0.72/api/v1/template//start', headers=_HEADERS)
    data = json.loads(r.text).get('data')


def test_get_activities():
    r = requests.post('http://192.168.0.72/api/v1/activitys/', headers=_HEADERS)
    data = json.loads(r.text).get('data')




def test_logout():
    r = requests.post('http://192.168.0.72/api/v1/user/logout', headers=_HEADERS)
    assert r.status_code == 200
