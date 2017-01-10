# -*- coding: utf-8 -*-
import time
import logging
from luckycommon.cache import ProxyAgent, prefix_key
from luckycommon.utils.exceptions import CacheError


_LOGGER = logging.getLogger('lucky')
_LOCK_TIMEOUT = 3


def cache_lock(lock_timeout=_LOCK_TIMEOUT):
    def _cache_lock(func):
        def _wrap(lock_id, *args, **kwargs):
            lock = 0

            while lock != 1:
                now_time = int(time.time())
                timestamp = now_time + lock_timeout + 1
                expire_time = timestamp
                # try to get lock for identified lock_id
                lock = _try_lock(lock_id, timestamp)
                if lock == 1:
                    break
                else:
                    out_time = _get_lock_state(lock_id)
                    if out_time and now_time > int(out_time):
                        tmp_time = _getset_lock(lock_id, timestamp)
                        if not tmp_time or now_time > int(tmp_time):
                            break
                # sleep 10ms
                _LOGGER.debug('got lock failed! try to sleep a while...')
                time.sleep(0.01)

            try:
                ret = func(lock_id, *args, **kwargs)
            except Exception as e:
                _LOGGER.error('cache lock do func error, %s' % e)

            # try to release lock
            now_time = int(time.time())
            if now_time < expire_time:
                _release_lock(lock_id)
            else:
                _LOGGER.warn('job time out, lock has been '
                             'acquired by other session')

            return ret
        return _wrap
    return _cache_lock


def _try_lock(lock_id, timestamp):
    try:
        lock_key = prefix_key('lock:activity:%s' % lock_id)
        return ProxyAgent().setnx(lock_key, timestamp)
    except Exception as e:
        _LOGGER.error('Redis setnx fail when try_lock.%s' % e)
        raise CacheError(e)


def _get_lock_state(lock_id):
    try:
        lock_key = prefix_key('lock:activity:%s' % lock_id)
        return ProxyAgent().get(lock_key)
    except Exception as e:
        _LOGGER.error('Redis get fail when get_lock_state.%s' % e)
        raise CacheError(e)


def _getset_lock(lock_id, timestamp):
    try:
        lock_key = prefix_key('lock:activity:%s' % lock_id)
        return ProxyAgent().getset(lock_key, timestamp)
    except Exception as e:
        _LOGGER.error('Redis getset fail when getset_lock.%s' % e)
        raise CacheError(e)


def _release_lock(lock_id):
    try:
        lock_key = prefix_key('lock:activity:%s' % lock_id)
        ProxyAgent().delete(lock_key)
    except Exception as e:
        _LOGGER.error('Redis delete fail when release_lock.%s' % e)
        raise CacheError(e)
