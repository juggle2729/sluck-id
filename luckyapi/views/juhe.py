# -*- coding: utf-8 -*-
import logging

from luckycommon.third.juhe import check_notify_sign

from django.views.decorators.http import require_POST
from django.http import HttpResponse


_LOGGER = logging.getLogger('juhe')


@require_POST
def juhe_callback(request):
    try:
        check_notify_sign(request)
        # we must return 'success' after processing
        return HttpResponse('success', status=200)
    except Exception as e:
        _LOGGER.exception('juhe callback exception.(%s)' % e)
        return HttpResponse('failed', status=500)
