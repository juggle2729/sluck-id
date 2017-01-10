# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta, tzinfo

from django.conf import settings

ZERO_TIME_DELTA = timedelta(0)

# 北京时间，若是其它国家，这里要改成相应的offset
LOCAL_TIME_DELTA = timedelta(hours=settings.TIME_OFFSET)


class UTC(tzinfo):
    """实现了格林威治的tzinfo类"""

    def utcoffset(self, dt):
        return ZERO_TIME_DELTA

    def dst(self, dt):
        return ZERO_TIME_DELTA


class LocalTimezone(tzinfo):
    def utcoffset(self, dt):
        return LOCAL_TIME_DELTA

    def dst(self, dt):
        return ZERO_TIME_DELTA

    def tzname(self, dt):
        return ''


def utc_to_local(dt):
    return dt.replace(tzinfo=UTC()).astimezone(LocalTimezone())


def local_now():
    return utc_to_local(datetime.utcnow())


def get_utc_date(date=None):
    '''date is %Y-%m-%d str'''
    if date is None:
        # date for beijing timezone
        date = local_now().strftime('%Y-%m-%d')

    return local_to_utc(
        datetime.strptime(date, "%Y-%m-%d")).replace(tzinfo=None)


def utc_to_local_str(dt):
    if not dt:
        return ''
    return dt.replace(
        tzinfo=UTC()).astimezone(LocalTimezone()).strftime('%Y-%m-%d %H:%M:%S')


def local_to_utc(dt):
    return dt.replace(tzinfo=LocalTimezone()).astimezone(UTC())


def local_to_utc_str(dt):
    return dt.replace(
        tzinfo=LocalTimezone()).astimezone(UTC()).strftime('%Y-%m-%d %H:%M:%S')


def now_ts():
    return int(time.mktime(datetime.utcnow().timetuple()))


def to_ts(dt):
    return int(time.mktime(dt.timetuple()))


def to_local_ts(dt):
    return int(time.mktime(local_to_utc(dt).timetuple()))


def now_milli_ts():
    return int(time.time() * 1000)


def format_seconds(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '%d:%02d:%02d' % (h, m, s)


def left_seconds_today():
    tomorrow = local_now() + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=0, minute=0, second=0)
    return int(time.mktime(local_to_utc(tomorrow).timetuple())) - int(
        time.mktime(datetime.utcnow().timetuple()))


def adjust_ts(pay_at, delta_seconds=3):
    return pay_at + timedelta(seconds=delta_seconds)


def ts_to_local_date_str(ts, f='%Y-%m-%d'):
    dt = utc_to_local(datetime.fromtimestamp(ts))
    return dt.strftime(f)


def today_str():
    return utc_to_local(datetime.utcnow()).strftime('%Y-%m-%d')


def dt_to_ts(dt):
    return int(time.mktime(dt.timetuple()))
