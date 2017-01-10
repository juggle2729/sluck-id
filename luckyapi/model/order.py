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
        'numbers': list, #号码列表
        'status': int, #订单状态
        'receipt_info': basestring, #订单物流信息
        'time': basestring, #夺宝时间
    }

	
class BuyRecordLite(BaseModel):
    structure = {
        'uid': basestring, #user_id
        'avatar': basestring, #avar url
        'nick_name': basestring, #nick name
        'ip': basestring, #ip
        'addr': basestring, #address
        'numbers': list, #号码列表
        'num_count': int, #号码列表
        'order_id': long,
        'order_id_str': basestring,
        'status': int, #订单状态
        'time': basestring, #夺宝时间
    }


class OrderRecord(BaseModel):
    structure = {
        'user_id': basestring,
        'activity_id': basestring,
        'quantity': int,
        'price': float,
        'lucky_numbers': list
    }
