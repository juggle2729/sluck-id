# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.activity import ActivityWin, UserActivity, Activity

activity_win_query = ActivityWin.query.filter().order_by(ActivityWin.updated_at.desc()).all()

for item in activity_win_query:
    user_id = item.winner
    activity_id = item.activity_id
    user_activity = UserActivity.query.filter(UserActivity.user_id == user_id).filter(UserActivity.activity_id == activity_id).first()
    user_numbers = user_activity.numbers.split(',')
    activity = Activity.query.filter(Activity.id == activity_id).first()
    if not activity:
        continue
    if len(user_numbers) == activity.target_amount:
        print '%s user: %s, buy all in activity: <%s, %s>' % (user_activity.updated_at, user_id, activity.template_id, activity_id)
