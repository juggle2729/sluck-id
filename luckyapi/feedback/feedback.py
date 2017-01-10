# -*- coding: utf-8 -*-
import logging

from luckycommon.feedback.model.feedback import *
from luckycommon.feedback.db import feedback as feedback_db

from luckycommon.push import handler as push_handler

from luckycommon.utils.api import parse_p
from luckycommon.utils.decorator import response_wrapper

from django.views.decorators.http import require_POST


_LOGGER = logging.getLogger('lucky')


@require_POST
@response_wrapper
def feedback(request):
    """
    提交反馈
    """
    user_id = request.user_id
    tracks = parse_p(request.GET.get('p'))
    chn = tracks.get('chn', None)
    cvc = int(tracks.get('cvc', 0))
    qq = request.POST.get('qq')
    content = request.POST.get('content')
    content = content[:300]
    feedback_db.submit(qq, content, chn=chn, cvc=cvc, user_id=user_id)
    return {}
