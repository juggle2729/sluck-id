# -*- coding: utf-8 -*-

import logging
import urllib
import requests

from django.conf import settings
from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction, add_pay_fail_transaction


_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')


VERIFY_URL = settings.PAYPAL_VERIFY_URL_TEST


def verify_ipn_message(request):

    # parse POST
    params_str = urllib.unquote(request.POST)
    params_str = params_str.strip().rstrip()
    params = []
    for parem in params_str.split('&'):
        param_list = parem.split('=')
        params.append((param_list[0], param_list[1]))
    _LOGGER.info('Paypal INP message: %s', params)

    # Add '_notify-validate' parameter
    params.append(('cmd', '_notify-validate'))

    # Post back to PayPal for validation
    headers = {'content-type': 'application/x-www-form-urlencoded', 'host': 'www.paypal.com'}
    r = requests.post(VERIFY_URL, params=params, headers=headers, verify=True)
    r.raise_for_status()

    # Check return message and take action as needed
    if r.text == 'VERIFIED':
        _LOGGER.info('Paypal INP message verify result is VERIFIED')
    elif r.text == 'INVALID':
        _LOGGER.info('Paypal INP message verify result is INVALID')
    else:
        _LOGGER.info('Paypal INP message verify Error')