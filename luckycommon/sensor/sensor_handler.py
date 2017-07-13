# -*- coding: utf-8 -*-
from django.conf import settings

from luckycommon.sensor.sensor_db import sensor_status
from luckycommon.utils.api import parse_p


def get_sensor_status(platform, build_number):
    return sensor_status(platform, build_number)


def filter_apples(request, item_list):
    tracks = parse_p(request.GET.get('p'))
    chn = tracks.get('chn', None)
    cvc = int(tracks.get('cvc', 0))
    if chn == 'qg_ios':
        ios_sensor = get_sensor_status('ios', int(cvc))
        if ios_sensor:
            # filter apple goods
            filter_list = []
            for item in item_list:
                if item.get('gid') not in settings.APPLE_TIDS:
                    filter_list.append(item)
            return filter_list
    return item_list


def filter_gp(request, item_list):
    p = parse_p(request.GET.get('p'))
    gp_sensor = get_sensor_status('android', int(p.get('cvc', 0)))
    if p.get('market') == 'gp' and gp_sensor:
        filter_list = []
        for item in item_list:
            if int(item.get('gid')) in settings.GP_ALLOWED_TIDS:
                filter_list.append(item)
        return filter_list
    return item_list
