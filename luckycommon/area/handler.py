# -*- coding: utf-8 -*-
import json
import logging
import requests

from luckycommon.model import orm
from luckycommon.order.model.order import Area

_LOGGER = logging.getLogger('lucky')

AREA_API = 'http://AreaData.api.juhe.cn/AreaHandler.ashx?areaID=%s&action=getArea&key=dca9cb4edcc3a8d8f85f8da7f95af044'


def request_area_api(parent_id):
    request_api = AREA_API % parent_id
    try:
        r = requests.get(request_api)
        response_obj = json.loads(r.text)
        error_code = response_obj.get('code')
        if error_code != 0:
            _LOGGER.error('request area response error, %s', r.text)
            return []
        region_list = response_obj.get('str').get('regions')
        return region_list
    except Exception as e:
        _LOGGER.exception('request area api exception, %s', e)
    return []


def get_list_by_parent(parent_id):
    area_list = []
    items = Area.query.filter(Area.parent_id == parent_id).all()
    if not items:
        return []
        region_list = request_area_api(parent_id)
        for region in region_list:
            item = Area()
            item.id = region['id']
            item.name = region['name']
            item.full_name = region['FullName']
            item.parent_id = region['ParentId'] or '0'
            item.zip_code = region['zip']
            item.save(auto_commit=False)
            items.append(item)
        orm.session.commit()
        _LOGGER.info('save %s regions to db', len(region_list))
    for item in items:
        area_list.append({
            'id': item.id,
            'name': item.name,
            'full_name': item.full_name,
            'parent_id': item.parent_id
        })
    return area_list
