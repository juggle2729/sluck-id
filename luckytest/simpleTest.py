import json
import requests


def log(status, msg):
    print "*** %s, %s" % ('PASS' if status else 'FAILED', msg)


class LuckyAPIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = None
        self.uid = None
        self.token = None
        self.nickname = None
        self.country = None
        self.balance = None
        self.avatar_id = None
        self.email = None

    def login(self, phone_number, password):
        response = requests.post(self.base_url + '/api/v1/user/login',
                                 data=json.dumps({'phone': phone_number, 'password': password}))
        status = json.loads(response.text).get('status')
        if response.status_code == 200 and status == 0:
            data = json.loads(response.text).get('data')
            self.uid = data['id']
            self.token = data['token']
            self.nickname = data['nick_name']
            self.country = data['country']
            self.balance = data['balance']
            self.avatar_id = data['avatar_id']
            self.email = data['email']
            self.headers = {
                'X-AUTH-USER': self.uid,
                'X-AUTH-TOKEN': self.token
            }
            return True
        else:
            return False

    def get_pay_types(self, platform, version_code, locale):
        response = requests.get(self.base_url + '/api/v1/pay/types',
                                headers=self.headers,
                                params={'platform': platform,
                                        'version_code': version_code,
                                        'locale': locale
                                        })
        if response.status_code == 200:
            data = json.loads(response.text).get('data')
            l = [item['pay_type'] for item in data['list']]
            return data['count'], l


if __name__ == '__main__':

    client = LuckyAPIClient('http://121.41.6.238')
    if (client.login('13971125425', '333333')):
        log(True, 'Login successfully')
    else:
        log(False, 'Login failed')
    param_list = [dict(platform=x, version_code=y, locale=z) for x, y, z in [
        ('android', 0, 'cn'),
        ('android', 1, 'cn'),
        ('android', 2, 'cn'),
        ('android', 3, 'cn'),
        ('android', 4, 'cn'),
        ('android', 1, 'us'),
        ('web', 0, 'cn'),
        ('web', 1, 'cn'),
        ('web', 2, 'cn'),
    ]]
    result_list = [
        (1, [2]),
        (1, [2]),
        (1, [2]),
        (1, [2]),
        (2, [2, 7]),
        (0, []),
        (1, [11]),
        (1, [11]),
        (1, [11]),
    ]

    for i in range(0, len(param_list)):
        if client.get_pay_types(**param_list[i]) == result_list[i]:
            log(True, 'Get pay types for %s' % param_list[i])
        else:
            log(False, 'Get pay types for %s' % param_list[i])

