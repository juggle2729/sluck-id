# -*- coding: utf-8 -*-

from luckyapi.model import BaseModel
from luckyapi.model.activity import Revealed


class ShowLite(BaseModel):
    structure = {
        'id': int,
        'gid': int,
        'term': int,
        'unit': int,
        'goods': {
            'name': basestring,
            'desc': basestring,
            'cover': basestring
        },
        'winner': {
            'uid': basestring,
            'avatar': basestring,
            'nick_name': basestring,
        },
        'title': basestring,
        'content': basestring,
        'images': basestring,
        'status': int,
        'show_time': basestring,
        'verified_at': int
    }


class ShowDetail(BaseModel):
    structure = {
        'id': int,
        'gid': int,
        'term': int,
        'unit': int,
        'price': int,
        'goods': {
            'name': basestring,
            'desc': basestring,
            'cover': basestring
        },
        'title': basestring,
        'content': basestring,
        'images': basestring,
        'status': int,
        'show_time': basestring,
        'verified_at': int,
        'verify_comment': basestring,
        'revealed': Revealed, 
    }
