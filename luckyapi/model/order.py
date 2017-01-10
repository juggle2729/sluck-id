# -*- coding: utf-8 -*-
from luckyapi.model import BaseModel


class OrderDetail(BaseModel):
    structure = {
        'order_id': basestring,
        'activity_id': basestring,
        'quantity': int,
        'price': float,
        'uid': basestring, #user_id
        'ip': basestring, #ip
        'addr': basestring, #address
        'numbers': list, #�����б�
        'status': int, #����״̬
        'receipt_info': basestring, #����������Ϣ
        'time': basestring, #�ᱦʱ��
    }

	
class BuyRecordLite(BaseModel):
    structure = {
        'uid': basestring, #user_id
        'avatar': basestring, #avar url
        'nick_name': basestring, #nick name
        'ip': basestring, #ip
        'addr': basestring, #address
        'numbers': list, #�����б�
        'num_count': int, #�����б�
        'order_id': long,
        'order_id_str': basestring,
        'status': int, #����״̬
        'time': basestring, #�ᱦʱ��
    }


class OrderRecord(BaseModel):
    structure = {
        'user_id': basestring,
        'activity_id': basestring,
        'quantity': int,
        'price': float,
        'lucky_numbers': list
    }
