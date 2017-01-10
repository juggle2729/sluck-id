# -*- coding: utf-8 -*-
import logging

from luckycommon.cache import redis_cache
from luckycommon.db import activity as activity_db

from luckycommon.utils import id_generator
from luckycommon.utils.decorator import response_wrapper

from future.utils import raise_with_traceback

from django.views.decorators.http import require_GET


_LOGGER = logging.getLogger('lucky')
_DEFAULT_PAGE_SIZE = 20


@require_GET
@response_wrapper
def get_pk_activitys(request):
    """
    查看正在进行的pk场活动
    """
    pk_list = []
    pk_size = int(request.GET.get('pk_size', 2))
    page = int(request.GET.get('page', 0))
    size = int(request.GET.get('size', 0))
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    templates = activity_db.get_pk_templates(pk_size, offset, limit)
    for template in templates:
        current_term = template.current_term
        latest_id = id_generator.generate_uuid(
            'activity:%s:%s' % (template.id, current_term))
        unit_numbers = template.target_amount / pk_size
        current_numbers = template.target_amount - redis_cache.get_left_numbers_count(latest_id)
        applied_count = (current_term - 1) * pk_size + current_numbers / unit_numbers
        pk_list.append({
            'gid': template.id,
            'name': template.short_title,
            'cover': template.cover,
            'count': applied_count
        })
    return {
        'list': pk_list
    }
