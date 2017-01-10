# -*- coding: utf-8 -*-
import base64
import hashlib
import logging

import dicttoxml
import pyDes
import xmltodict
from suds.client import Client

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_CLIENT = Client('http://sandbox2.vtcebank.vn/WSCard2010/card.asmx?wsdl')
_MERCHANT_ID = '920130506'
_KEY = '920130506!@#123'


def _encrypt(string):
    m = hashlib.md5()
    m.update(_KEY)
    key = m.hexdigest()
    k = pyDes.triple_des(key[0:24], pyDes.ECB, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
    return base64.b64encode(k.encrypt(string))


def _decrypt(string):
    m = hashlib.md5()
    m.update(_KEY)
    key = m.hexdigest()
    k = pyDes.triple_des(key[0:24], pyDes.ECB, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
    return k.decrypt(base64.b64decode(str(string)))


def is_card_valid(card_id):
    post_data = {
        "Function": 'CheckCardStatus',
        "CardID": card_id,
        "CardCode": None,
        "Description": 'test',
    }
    xml_data = dicttoxml.dicttoxml(post_data, attr_type=False, custom_root='CardRequest')
    r = _CLIENT.service.Request(_MERCHANT_ID, _encrypt(xml_data))
    response_dict = xmltodict.parse(_decrypt(r), encoding='utf-8')
    response_status = response_dict.get('CardResponse').get('ResponseStatus')
    response_desc = response_dict.get('CardResponse').get('Descripton')
    if int(response_status) == 0:
        return True
    else:
        print response_status, response_desc
        return False


def consume_card(card_id, card_code):
    post_data = {
        "Function": 'UseCard',
        "CardID": card_id,
        "CardCode": card_code,
        "Description": 'consume',
    }
    xml_data = dicttoxml.dicttoxml(post_data, attr_type=False, custom_root='CardRequest')
    r = _CLIENT.service.Request(_MERCHANT_ID, _encrypt(xml_data))
    response_dict = xmltodict.parse(_decrypt(r), encoding='utf-8')
    response_status = response_dict.get('CardResponse').get('ResponseStatus')
    response_desc = response_dict.get('CardResponse').get('Descripton')
    if int(response_status) == 0:
        return True
    else:
        print response_status, response_desc
        return False


if __name__ == '__main__':
    print is_card_valid('PM0000025055')
    print consume_card('PM0000025055', '363553245267')
