# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from celery import Celery, platforms
from kombu import Queue, Exchange
from django.conf import settings


class MyRouter(object):

    def route_for_task(self, task, *args, **kwargs):
        if task.startswith('activity'):
            return {'queue': 'async_activity', 'routing_key': 'async_activity'}
        if task.startswith('campaign'):
            return {'queue': 'async_campaign', 'routing_key': 'async_campaign'}
        if task.startswith('partner'):
            return {'queue': 'async_partner', 'routing_key': 'async_partner'}
        if task.startswith('utils'):
            return {'queue': 'async_utils', 'routing_key': 'async_utils'}


QUEUES = (
    Queue('async_activity', Exchange('event'),
          routing_key='async_activity'),
    Queue('async_campaign', Exchange('async_campaign'),
          routing_key='async_campaign'),
    Queue('async_partner', Exchange('async_partner'),
          routing_key='async_partner'),
    Queue('async_utils', Exchange('async_utils'),
          routing_key='async_utils'),
)


platforms.C_FORCE_ROOT = True


app = Celery('async',
             broker=settings.CELERY_BROKER,
             include=['luckycommon.async.async_job'])

app.conf.update(CELERY_ACCEPT_CONTENT=['pickle', ],
                CELERY_IGNORE_RESULT=True,
                CELERY_DISABLE_RATE_LIMITS=True,
                CELERY_DEFAULT_EXCHANGE='default',
                CELERY_DEFAULT_QUEUE='default',
                CELERY_DEFAULT_ROUTING_KEY='default',
                CELERY_DEFAULT_EXCHANGE_TYPE='topic',
                CELERY_TASK_SERIALIZER='pickle',
                CELERY_RESULT_SERIALIZER='pickle',
                BROKER_HEARTBEAT=10,
                CELERY_QUEUES=QUEUES,
                CELERY_ROUTES=(MyRouter(),),
                CELERYD_HIJACK_ROOT_LOGGER = False, )

if __name__ == "__main__":
    app.start()
