# -*- coding: utf-8 -*-
from luckycommon.sensor.sensor_model import SensorSwitch
from luckycommon.utils.decorator import sql_wrapper


@sql_wrapper
def get_sensor_status(platform, build_number):
    sensor_switch = SensorSwitch.query.filter(
        SensorSwitch.platform == platform).filter(
        SensorSwitch.build_number == build_number
    ).first()
    if not sensor_switch:
        return False
    return sensor_switch.sensor_status
