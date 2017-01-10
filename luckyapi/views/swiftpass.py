# -*- coding: utf-8 -*-
import logging

from luckycommon.third import swiftpass

from django.views.decorators.http import require_POST
from django.http import HttpResponse

_LOGGER = logging.getLogger('pay')


@require_POST
def swiftpass_notify(request):
    try:
        swiftpass.check_notify_sign(request)
        # we must return 'success' after processing
        return HttpResponse('success', status=200)
    except Exception as e:
        _LOGGER.exception('swiftpass notify exception.(%s)' % e)
        return HttpResponse('failure', status=400)
