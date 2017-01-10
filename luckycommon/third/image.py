# -*- coding: utf-8 -*-

import logging
from django.conf import settings
from qiniu import (Auth, BucketManager, put_data, urlsafe_base64_decode,
                   build_batch_delete)

from luckycommon.utils.exceptions import ServerError
from luckycommon.utils.id_generator import generate_uuid

_LOGGER = logging.getLogger('lucky')
EXPIRE_TIME = 365 * 24 * 3600   # 1 year

Q = Auth(*(settings.QINIU_KEY_PAIR))


def get_token(bucket=settings.ADMIN_BUCKET_NAME, expires=EXPIRE_TIME):
    token = Q.upload_token(bucket, expires=expires)

    return token


def delete_data_by_url(urls, bucket=settings.ADMIN_BUCKET_NAME, key_prefix=''):
    keys = []
    for url in urls:
        if not url.endswith('/'):
            url += '/'
        key = url.split('/')[-2]
        if key_prefix:
            key = '%s/%s' % (key_prefix, key)
        keys.append(key)
    delete_data_by_key(keys, bucket)


def delete_data_by_key(keys, bucket):
    ops = build_batch_delete(bucket, keys)
    b = BucketManager(Q)
    b.batch(ops)


def upload_data(data, bucket=settings.USER_BUCKET_NAME, key_prefix='',
                mime_type='application/octet-stream', check_crc=True,
                use_base64=True):
    name = generate_uuid()
    # for small data only...
    if use_base64:
        data = urlsafe_base64_decode(str(data))

    token = get_token(bucket)
    if key_prefix and not key_prefix.endswith('/'):
        key_prefix += '/'
    key = '%s%s' % (key_prefix, name)
    b = BucketManager(Q)
    b.delete(bucket, key)
    ret, info = put_data(token, key, data, mime_type=mime_type,
                         check_crc=check_crc)

    if not ret or ret.get('key') != key:
        _LOGGER.error('fail to upload image, info: %s', info)
        raise ServerError('fail to upload image to qiniu')

    url = settings.QINIU_DOMAIN + key
    return url

if __name__ == '__main__':
    import base64
    with open('/tmp/test.png') as img:
        data = base64.b64decode(img.read())
        print upload_data(data)
