# -*- coding: utf-8 -*-

from luckyapi.model import BaseModel


class TransactionLite(BaseModel):
    structure = {
        'status': int,
        'title': basestring,
        'price': float,
        'balance': float,
        'time': basestring
    }

