# -*- coding: utf-8 -*-

from luckyapi.model import BaseModel


class Account(BaseModel):
    structure = {
        'phone': str,
        'nick_name': basestring,
        'password': str,
        'email': str,
        'country': str,
    }

    required_fields = ['phone', 'password']
    default_fields = {
        'nick_name': '',
        'email': '',
        'country': ''
    }
