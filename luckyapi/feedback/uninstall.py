# -*- coding: utf-8 -*-

import logging
import json

from django.views.decorators.http import require_POST
from django.utils.encoding import smart_unicode

from luckycommon.stats.device_track import (create_device_track,
                                            update_uninstall_reason)
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import check_params

_LOGGER = logging.getLogger(__name__)


@require_POST
@response_wrapper
def create_device_stats(req):
    params = json.loads(smart_unicode(req.body))
    check_params(params, ['aid', 'type', 'run_count'])
    create_device_track(params)

    return {}


@require_POST
@response_wrapper
def create_uninstall_reason(req):
    params = json.loads(smart_unicode(req.body))
    _LOGGER.debug('parameters are: %s' % params)
    check_params(params, ['aid', 'reason'])
    update_uninstall_reason(params)

    return {}
