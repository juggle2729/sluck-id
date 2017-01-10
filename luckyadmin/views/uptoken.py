# -*- coding: utf-8 -*-
from django.conf import settings
from django.views.decorators.http import require_GET, require_POST
from luckycommon.third.image import get_token, delete_data_by_url
from luckycommon.utils.api import JsonResponse, token_required, check_auth
from luckycommon.utils.decorator import response_wrapper


@require_GET
# if use decorator here, qiniu sdk will error...
def get_uptoken(req):
    check_auth(req)
    bucket = req.GET.get('bucket', settings.ADMIN_BUCKET_NAME)
    if bucket == 'avatar':
        bucket = settings.USER_BUCKET_NAME
    token = get_token(bucket)

    return JsonResponse({'uptoken': token})


@require_POST
@response_wrapper
@token_required
def delete_image(req):
    urls = req.POST.get('urls')
    urls = urls.split(',')
    delete_data_by_url(urls)

    return {}
