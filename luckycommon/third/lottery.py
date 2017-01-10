# -*- coding: utf-8 -*-
import time
import logging
from datetime import datetime

from django.conf import settings


_LOGGER = logging.getLogger(__name__)


def calc_announce_delay(activity_id=None):
    debug_delay = settings.ANNOUNCE_DELAY
    return debug_delay
