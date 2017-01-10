#! -*- coding:utf-8 -*-
from luckycommon.account.model.account import Account, AccountToken


class TokenBackend(object):

    def authenticate(self, user_id, token):
        return None


