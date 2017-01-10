# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import datetime

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.activity import HotActivity, ActivityTemplate, Activity


hot_items = HotActivity.query.all()
for hot_item in hot_items:
    template_id = hot_item.template_id
    first_activity = Activity.query.filter(Activity.template_id == template_id).filter(Activity.term_number == 1).first()
    hot_item.added_at = first_activity.created_at
    hot_item.save()


template_items = ActivityTemplate.query.all()
for template in template_items:
    template_id = template.id
    first_activity = Activity.query.filter(Activity.template_id == template_id).filter(Activity.term_number == 1).first()
    if first_activity:
        template.added_at = first_activity.created_at
        template.save()
    
