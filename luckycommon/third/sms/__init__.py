# -*- coding: utf-8 -*-


class SMSSender(object):

    """base class for sms platforms"""

    def send_sms(self, phone_nums, template_id, params, use_unicode=True):
        raise Exception('this is an abstract class!')
