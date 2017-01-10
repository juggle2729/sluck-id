# -*- coding: utf-8 -*-
"""
DB Model, used for ORM
"""
from luckycommon.utils.orm import ArmoryOrm
from django.conf import settings


orm = ArmoryOrm()
orm.init_conf(settings.MYSQL_CONF)
slave = ArmoryOrm()
slave.init_conf(settings.SLAVE_CONF)
