# -*- coding: utf-8 -*-
import importlib
from django.conf import settings


CMD_MODULES = {
    '11#%s/user/newbie_task' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.mission.fresh_mission'),
    '11#%s/discovery/first_double_charge' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.campaign.first_double'),
    '11#%s/discovery/compensate' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.campaign.miss_return'),
    '11#%s/user/my_daily_attendance' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.mission.daily_sign'),
}
