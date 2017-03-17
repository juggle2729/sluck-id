# -*- coding: utf-8 -*-
from importlib import import_module

from django.conf import settings

_URL = settings.WEB_APP_ROOT_URL

COMPLETE_DISMISS_COMMANDS = {
    '11#%s/user/newbie_task' % _URL: import_module('luckycommon.mission.fresh_mission'),
    '11#%s/discovery/first_double_charge' % _URL: import_module('luckycommon.campaign.first_double'),
    '7#666': import_module('luckycommon.campaign.miss_return'),
    '11#%s/user/my_daily_attendance' % _URL: import_module('luckycommon.mission.daily_sign'),
    '11#%s/discovery/winprize' % _URL: import_module('luckycommon.campaign.quiz_controller'),
}

ONLY_FOR_NEWBIE_COMMANDS = [
    '11#%s/guide' % _URL,
]
