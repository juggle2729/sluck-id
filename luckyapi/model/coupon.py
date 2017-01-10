# -*- coding: utf-8 -*-

from luckyapi.model import BaseModel


class CouponLite(BaseModel):
    structure = {
        'id': int,
        'title': basestring,
        'desc': basestring,
        'price': int,
        'status': int,
        'start_date': basestring,
        'end_date': basestring,
    }

