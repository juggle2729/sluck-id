# -*- coding: utf-8 -*-
import pyDes
import string
from hashlib import md5


REQUEST_URL = 'http://ccapi.kamenwang.com/Interface/Method?'
#REQUEST_URL = 'http://ccapi.kabaling.com/Interface/Method?'
#APP_ID = '801000'
#APP_KEY = 'F636297CB44B2F02BA4651282266EC2F'
APP_ID = '802912'
APP_KEY = 'BDCD4367751A33A973231F51C2DEDA7B'
LEAST_STOCK = 5


def card_decrypt(third_id, input_num):
    key_str = str(third_id) + APP_KEY
    key = md5(key_str).hexdigest()[4:12]
    DES_COM = pyDes.des(key, pyDes.CBC, '\0\0\0\0\0\0\0\0')
    output = DES_COM.decrypt(input_num.decode('base64'))
    return filter(lambda x: x in string.printable, output)


if __name__ == '__main__':
    import sys
    third_id = sys.argv[1]
    input_num = sys.argv[2]
    card_decrypt(third_id, input_num)
