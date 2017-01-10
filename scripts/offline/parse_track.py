# -*- coding: utf-8 -*-
from io import open
import os
import argparse
import json
import gzip
import contextlib
from datetime import datetime, timedelta
from dateutil import tz

from redis import StrictRedis
from pymongo import MongoClient
from pymongo.errors import PyMongoError

LOG_PATH = '/tmp/'
MONGO_NODE = '127.0.0.1:27017'
VALID_TYPE = ('login', 'register', 'pay', 'recharge', 'win')
CACHE = []


def get_redis():
    if ('redis_conn_inst' not in globals()):
        globals()['redis_conn_inst'] = StrictRedis()
    return globals()['redis_conn_inst']


def get_mongo():
    if ('mongo_conn_inst' not in globals()):
        globals()['mongo_conn_inst'] = MongoClient(
            MONGO_NODE).lucky
    return globals()['mongo_conn_inst']


@contextlib.contextmanager
def patch_gzip_for_partial():
    """
    Context manager that replaces gzip.GzipFile._read_eof with a no-op.

    This is useful when decompressing partial files, something that won't
    work if GzipFile does it's checksum comparison.

    """
    _read_eof = gzip.GzipFile._read_eof
    gzip.GzipFile._read_eof = lambda *args, **kwargs: None
    yield
    gzip.GzipFile._read_eof = _read_eof


def clean_data(d):
    r = get_redis()
    if 'user_id' not in d or r.sismember('lucky:virtual:account', d['user_id']):
        return {}
    ts = datetime.strptime(d.pop('@timestamp'), "%Y-%m-%dT%H:%M:%S.%f")
    t = d['type']
    data = {
        '_id': d['user_id'],
        '$set': {},
        '$inc': {}
    }
    if t == "register":
        data['$set']['created_at'] = ts
        data['$set']['aid'] = d.get('aid', 'none')
        data['$set']['chn'] = d.get('chn', 'none')
    elif t == "login" and not d['logon']:
        data['$set']['first_login_at'] = ts
    elif t == 'win':
        if 'first_win_cost' in d:
            data['$set']['win.first_time'] = ts
            mg = get_mongo()
            saved = mg.user_stats.find_one({
                'id': d['user_id']
            })
            if saved:
                data['$set']['win.first_cost'] = saved.get('recharge', {}).get(
                    'total', 0)
            else:
                data['$set']['win.first_cost'] = 0
        else:
            data['$inc']['win.total'] = float(d.get('activity_target', 0))
    if t == 'pay':
        data['$inc']['pay.count'] = 1
        data['$inc']['pay.total'] = float(d['price'])
    if t == 'recharge':
        data['$inc']['recharge.' + d['channel']] = float(d['price'])
        data['$inc']['recharge.total'] = float(d['price'])

    to_zone = tz.gettz('Asia/Shanghai')
    from_zone = tz.gettz('UTC')
    from_ts = ts.replace(tzinfo=from_zone)
    data['key'] = '%s-%s' % (d['user_id'],
                             from_ts.astimezone(to_zone).strftime("%Y-%m-%d"))
    data['$set']['updated_at'] = ts

    return data


def _save(ds):
    db = get_mongo()
    day_bulk = db.daily_stats.initialize_unordered_bulk_op()
    total_bulk = db.user_stats.initialize_unordered_bulk_op()
    for d in ds:
        data = {}
        for k in '$inc', '$set':
            if d.get(k):
                data[k] = d[k]
        day_bulk.find(
            {'_id': d['key'], 'user_id': d['_id']}).upsert().update_one(data)
        total_bulk.find(
            {'_id': d['_id']}).upsert().update_one(data)
    day_bulk.execute()
    total_bulk.execute()


def save(data):
    global CACHE
    CACHE.append(data)
    if len(CACHE) > 1000:
        try_count = 0
        while try_count < 3:
            try:
                _save(CACHE)
                CACHE=[]
                return
            except PyMongoError as e:
                print 'ERROR, save error', e
                try_count += 1

def test_save(d):
    db = get_mongo()
    data = {}
    for k in '$inc', '$set':
        if d.get(k):
            data[k] = d[k]
    db.daily_stats.update_one({'_id': d['key'], 'user_id': d['_id']}, data, upsert=True)
    db.user_stats.update_one({'_id': d['_id']}, data, upsert=True)


def parse_and_import(filename):
    print "parsing", filename
    with patch_gzip_for_partial():
        source = gzip.open(filename) if filename.endswith('.gz') else open(
            filename)
        for line in source:
            try:
                data = json.loads(line)
            except (ValueError, TypeError) as e:
                print e
                continue

            if 'type' not in data or data['type'] not in VALID_TYPE:
                continue

            d = clean_data(data)
            if d:
                save(d)


def main():
    parser = argparse.ArgumentParser(
        description=('script to parse lucky tracker log'),
        add_help=True)
    parser.add_argument(
        'chosen_date', nargs='?',
        default=(datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d'),
        help='Date you want, format is %%Y-%%m-%%d. For example:2015-6-24.'
        'Default is yesterday.')

    args = parser.parse_args()
    chosen_date_str = args.chosen_date
    filename_prefix = 'track.json'
    for f in os.listdir(LOG_PATH):
        if f.startswith(filename_prefix):
            parse_and_import(os.path.join(LOG_PATH, f))

if __name__ == '__main__':
    main()
