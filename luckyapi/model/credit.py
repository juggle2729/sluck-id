# -*- coding: utf-8 -*-

from luckyapi.model import BaseModel


class RecordLite(BaseModel):
    structure = {
        'title': basestring,
        'amount': float,
        'time': basestring
    }
