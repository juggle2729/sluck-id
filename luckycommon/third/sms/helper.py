# -*- coding: utf-8 -*-
import logging

from luckycommon.third.sms.esms import ESMSSender
#from luckycommon.third.sms.vmg_sms import VMGSMSSender
from luckycommon.third.sms.nexmo import NexmoSender

_LOGGER = logging.getLogger(__name__)


def send_sms(phone_nums, template_name, params=None, country=None):
    prefixed_phone_nums = ['62' + item for item in phone_nums]
    _LOGGER.error('ready to send sms, %s', prefixed_phone_nums)
    # sender = VMGSMSSender()
    # sender = ESMSSender()
    sender = NexmoSender()
    sender.send_sms(prefixed_phone_nums, template_name, params)
