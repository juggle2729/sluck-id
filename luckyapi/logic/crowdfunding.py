# -*- coding: utf-8 -*-
import re
import json
import time
import random
import logging

from luckyapi.model.activity import ActivityDetail, ActivityLite, Revealed, CalcRecord

from luckycommon.cache import redis_cache
from luckycommon.account.db.account import get_account
from luckycommon.db.goods import get_goods
from luckycommon.db.activity import *
from luckycommon.level.handler import get_user_level
from luckycommon.order.db.order import get_order, get_awarded_order
from luckycommon.model.activity import TEMPLATE_STATUS, ACTIVITY_STATUS

from luckycommon.pay import handler as pay_handler
from luckycommon.event import handler as event_handler
from luckycommon.async.async_job import new_activity_index, buy_one

from luckycommon.utils import id_generator
from luckycommon.utils.api import EnhencedEncoder
from luckycommon.utils.tz import utc_to_local, now_ts
from luckycommon.utils.exceptions import (AuthenticateError, ResourceInsufficient,
                                          ParamError, DataError, CacheError)

from future.utils import raise_with_traceback
from django.conf import settings


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')

_ADMIN_USER_ID = 1L
_DELAY_CHECK_SECONDS = 3600
_DEFAULT_PAGE_SIZE = 10
_MAX_PAGE_SIZE = 20

_UUID_RE = re.compile(
    r'^[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}$')


def create_activity_template(user_id, template):
    # check account validation
    # if user_id != _ADMIN_USER_ID:
    #    raise AuthenticateError("only admin can do operation")

    # check goods validation
    goods = get_goods(template.goods_id)
    if not goods:
        raise_with_traceback(ParamError("goods id wrong"))

    template = create_template(template)

    return template


def get_user_numbers(user_id, activity_id, user_activity=None):
    # TODO: 这里没有必要取所有的号码，限制长度
    user_activity = user_activity or get_user_activity(user_id, activity_id)
    if not user_activity or not user_activity.numbers:
        return []
    return user_activity.numbers.split(',')


def _query_announce_countdown(activity):
    extend = {} if not activity.extend else json.loads(activity.extend)
    announce_ts = extend['announce_ts']
    countdown_ts = announce_ts - now_ts()
    countdown_ts = 0 if countdown_ts < 0 else countdown_ts * 1000
    return countdown_ts


def get_revealing(activity):
    revealing = {}
    revealing.update({'remain_ms': _query_announce_countdown(activity)})
    extend = {} if not activity.extend else json.loads(activity.extend)
    revealing.update({
        'calc': {
            'url': '',
            'result_a': '',
        }
    })
    return revealing


def get_revealed(activity, use_cache=False):
    if use_cache:
        revealed = redis_cache.get_revealed(activity.id)
        if revealed:
            revealed_dict = json.loads(revealed)
            account_id = revealed_dict['winner']['uid']
            try:
                account = get_account(account_id, use_cache=True)
                level_dict = get_user_level(account.id)
                revealed_dict['winner'].update({
                    'avatar': account.avatar_id,
                    'nick_name': account.nick_name,
                    'level': level_dict['current_level'],
                    'level_icon': level_dict['level_icon'],
                    'level_name': level_dict['level_name']
                })
                # TODO: 检查账户信息是否变更，删除相应的cache
            except:
                pass
            return revealed_dict

    revealed = {}
    revealed.update({'lucky_number': activity.winner})
    revealed.update({
        'reveal_time': utc_to_local(activity.announced_at).strftime('%Y-%m-%d %H:%M:%S')
    })
    win = get_activity_win(activity.id)
    if not win:
        info = {} if not activity.extend else json.loads(activity.extend)
        order_id = redis_cache.get_lucky_order(activity.id, activity.winner)
        revealed.update({'lucky_order': order_id})
    else:
        info = {} if not win.announce_info else json.loads(win.announce_info)
        revealed.update({'lucky_order': win.order_id})
    revealed.update({
        'calc': {
            'url': '',
            'result_a': info.get('result_a'),
        }
    })
    if info.get('winner'):
        winner_info = info['winner']
        # 以下代码为了保证兼容性
        winner_numbers = winner_info.get('numbers')
        if not winner_numbers:
            winner_num_count = winner_info.get('num_count')
            if winner_num_count:
                winner_numbers = [0] * winner_num_count

        revealed.update({
            'winner': {
                'uid': winner_info.get('uid'),
                'avatar': winner_info.get('avatar'),
                'nick_name': winner_info.get('nick_name'),
                'ip': winner_info.get('ip'),
                'addr': winner_info.get('addr'),
                'numbers': winner_numbers,
                'time': revealed['reveal_time']
            }
        })
    else:
        lucky_order = get_order(revealed['lucky_order'])
        lucky_user = get_account(lucky_order.buyer, use_cache=True)
        geo_info = {} if not lucky_order.extend else json.loads(
            lucky_order.extend)
        revealed.update({
            'winner': {
                'uid': lucky_user.id,
                'avatar': lucky_user.avatar_id,
                'nick_name': lucky_user.nick_name,
                'ip': geo_info.get('ip'),
                'addr': geo_info.get('addr'),
                'numbers': get_user_numbers(lucky_user.id, activity.id),
                'time': revealed['reveal_time']
            }
        })

    # save revealed dict to redis
    if use_cache:
        number_count = len(revealed['winner']['numbers'])
        del revealed['winner']['numbers']
        revealed['winner']['num_count'] = number_count
        revealed_info = json.dumps(
            revealed, cls=EnhencedEncoder, ensure_ascii=False)
        redis_cache.set_revealed(activity.id, revealed_info)
        return revealed

    return revealed


def create_activity_detail(user_id, activity, user_activity=None, use_cache=False):
    detail = ActivityDetail()
    detail.id = activity.id
    detail.gid = activity.template_id
    detail.term = activity.term_number
    detail.created_at = utc_to_local(
        activity.created_at).strftime('%Y-%m-%d %H:%M:%S')
    latest_term = get_latest_term(activity.template_id)
    detail.latest_term = latest_term
    detail.latest_id = id_generator.generate_uuid(
        'activity:%s:%s' % (activity.template_id, latest_term))
    detail.status = activity.status
    detail.goods = {
        'name': activity.name,
        'desc': activity.desc,
        'cover': activity.cover or activity.images.split(',')[0],
        'images': activity.images,
        'detail_url': None,
        'graphics': activity.graphics
    }
    detail.price = activity.price
    goods = get_goods(activity.goods_id)
    detail.is_resell = 1 if int(activity.target_amount) >= 1000 and goods.shipping_type==0 else 0
    if detail.is_resell:
        detail.resell_price_h = int(float(goods.price)*0.9*1000)
        detail.resell_price_l = int(float(goods.price)*0.8*1000)
    detail.unit = activity.unit
    detail.buy_limit = pay_handler.adjust_buy_limit(user_id, activity)
    detail.target_amount = activity.target_amount
    detail.current_amount = activity.current_amount
    if detail.status == ACTIVITY_STATUS.ANNOUNCE_READY:
        detail.revealing = get_revealing(activity)
    if detail.status == ACTIVITY_STATUS.ANNOUNCED:
        detail.revealed = get_revealed(activity, use_cache)
    detail.start_time = detail.created_at
    if user_id:
        my_numbers = get_user_numbers(user_id, activity.id, user_activity)
        show_numbers = my_numbers[:20]
        detail.my = {
            'numbers': show_numbers,
            'num_count': len(my_numbers)
        }
        if detail.status == ACTIVITY_STATUS.ANNOUNCED:
            winner = detail.revealed['winner']
            if user_id and winner['uid'] == user_id:
                order_id = detail.revealed['lucky_order']
                lucky_order = get_awarded_order(order_id)
                if not lucky_order:
                    lucky_order = get_order(order_id)
                detail.my.update(
                    {'order_id': order_id, 'status': lucky_order.status})

    detail.active_code = _fill_active_code(activity.template_id)
    # check pk
    if activity.pk:
        pk_info = get_pk_info(activity)
        latest_trend = get_pk_latest_trend(activity)
        detail.pk = {
            'size': activity.pk,
            'info': pk_info,
            'trend': latest_trend
        }
    # special case hard code for star activity
    if int(detail.gid) in (774, 775):
        detail.is_star = 1
        detail.star_desc = '''
Dalam rangka peluncuran TokoSeribu, kamu bisa mendapatkan kesempatan untuk makan malam di restoran mewah bersama salah satu selebriti online yang sedang naik daun. Mereka adalah Vania Gemash dan Donna Visca. 

Vania Gemash memiliki ratusan ribu militan follower di Instragram. Pose sensual dia yang menggemaskan akan bikin hati kamu meleleh.

Donna Visca adalah seorang gamer cewek yang kawaii. Ia adalah brand ambassador gaming gear ternama di Indonesia dan memiliki minat tinggi kepada Jepang.

Acara makan malam ini diadakan pada 21 Januari 2017 di Plaza Indonesia, Jakarta Pusat.

Jadi kamu pilih siapa, Vania Gemash yang seksi dan menggemaskan atau Donna Visca yang kawaii?

Syarat & Ketentuan:
1. TokoSeribu tidak bertanggung jawab atas transportasi dan akomodasi pemenang
2. Acara ini akan diadakan di Senju Omakase and Sake, Plaza Indonesia, Jakarta Pusat
3. TokoSeribu berhak untuk mengubah jadwal acara makan malam
4. Keputusan TokoSeribu tidak dapat diganggu gugat

        '''
    elif int(detail.gid) in (780, ):
        detail.is_star = 1
        detail.star_desc = '''
Keberangkatan tanggal 25 Maret 2017
Keindahan Belitung sudah tak diragukan lagi, maka tak heran jika pulau ini menjadi salah satu tujuan favorit para wisatawan. Salah satu objek wisata yang menjadi andalan Pulau Belitung adalah Pantai Tanjung Tinggi. Pantai ini semakin terkenal karena merupakan lokasi syuting film Laskar Pelangi. Pantai ini memiliki bebatuan besar yang dapat Anda naiki sambil menyaksikan pemandangan laut yang indah.

Selain itu Anda juga dapat mengunjungi pulau-pulau lainnya yang tak kalah indah, seperti Pulau Batu Berlayar dan Pulau Lengkuas untuk melakukan snorkeling atau hanya sekedar menikmati keindahan pantai. Dapatkan semua itu hanya di paket Belitung Long Weekend 4D3N By Citilink bersama Panorama Tours.

Rencana Perjalanan
Hari 1 Jakarta - Belitung by Citilink QG 9533 05.55 - 07.00
Hari 2 Island Hopping
Hari 3 Belitung Timur
Hari 4 Belitung - Jakarta By Citilink QG 9534 07.30 - 08.40

Paket Termasuk:
  Transportasi secara Seat In Coach (bergabung dengan penumpang lain)
  Local Guide
  Air mineral 1 botol per orang
  Life vest (pelampung)
  Alat snorkeling
  Transfer, tour dan makan sesuai itinerary
  3 Malam akomodasi sesuai hotel pilihan TokoSeribu termasuk sarapan
  Traditional boat ke Island Hoping
  1x Free Mie Khas Belitung
  Tiket pesawat Jakarta-Tanjung Pandan-Jakarta By Citilink (kelas ekonomi include bagasi 20 kg)

Paket Tidak Termasuk:
  Kunjungan tambahan (optional tour)
  Tipping porter, local guide dan supir
  Pengeluaran Pribadi (Minibar, Telephone, etc)
'''
    elif int(detail.gid) in (781, ):
        detail.is_star = 1
        detail.star_desc = '''
Keberangkatan tanggal 13 April 2017
Bali masih menjadi destinasi favorit para wisatawan. Saat musim liburan tiba, banyak wisatawan yang datang untuk berlibur ke Bali. Begitu pun pada saat libur di akhir pekan, Bali semakin ramai dan meriah dengan berbagai keseruan. Paket Bali Long Weekend 4D3N by Citilink dari Panorama Tours akan mengajak Anda menikmati akhir pekan yang spesial di Bali. Paket ini sudah termasuk pesawat terbang menggunakan Citilink dan juga fasilitas akomodasi di hotel pilihan beserta sarapan pagi.

Rencana Perjalanan
Hari 1 Jakarta - Denpasar By Citilink (QG 850 CGK 07.35 - DPS 10.30)
Hari 2 Bali Free Program
Hari 3 Bali Free Program
Hari 4 Denpasar - Jakarta By Citilink (QG 853 DPS 20.05 - CGK 21.00)

Paket Termasuk:
  Transportasi secara Seat In Coach (bergabung dengan penumpang lain)
  Transfer in/out Bandara
  3 Malam akomodasi sesuai hotel pilihan TokoSeribu termasuk sarapan
  Tiket pesawat Jakarta - Bali - Jakarta By Citilink (kelas ekonomi termasuk bagasi 20 kg)

Paket Tidak Termasuk:
  Kunjungan tambahan (optional tour)
  Tipping porter, local guide dan supir
  Pengeluaran Pribadi (Minibar, Telephone, etc)
'''

    return detail


def view_activity_detail(user_id, activity_id=None,
                         template_id=None, term_number=None, use_cache=False):
    if not activity_id and (not template_id or not term_number) or\
       (activity_id and not _UUID_RE.match(activity_id)):
        raise_with_traceback(ParamError('activity id invalid'))

    activity = get_activity(activity_id, template_id, term_number)
    if not activity:
        return {}
    detail = create_activity_detail(user_id, activity, use_cache=use_cache)
    return detail


def view_activity_lite(activity_id=None, template_id=None, term_number=None):
    if not activity_id and (not template_id or not term_number) or\
       (activity_id and not _UUID_RE.match(activity_id)):
        raise_with_traceback(ParamError('activity id invalid'))

    activity = get_activity(activity_id, template_id, term_number)
    lite = create_activity_lite(activity)
    return lite


def view_activity_revealed(activity_id=None):
    if not activity_id or\
       (activity_id and not _UUID_RE.match(activity_id)):
        raise_with_traceback(ParamError('activity id invalid'))

    activity = get_activity(activity_id)
    if activity.status != ACTIVITY_STATUS.ANNOUNCED:
        raise DataError('activity not revealed yet')
    revealed_dict = get_revealed(activity, use_cache=True)
    revealed = Revealed()
    revealed.activity_id = activity.id
    revealed.term = activity.term_number
    revealed.name = activity.name
    revealed.pk = activity.pk
    revealed.lucky_number = revealed_dict['lucky_number']
    revealed.reveal_time = revealed_dict['reveal_time']
    revealed.winner = revealed_dict['winner']
    return revealed


def view_latest_activity(user_id, template_id, lite_only=False, id_only=False):
    latest_term = get_latest_term(template_id)
    if id_only:
        latest_id = id_generator.generate_uuid(
            'activity:%s:%s' % (template_id, latest_term))
        return latest_id
    if not lite_only:
        return view_activity_detail(user_id, template_id=template_id, term_number=latest_term, use_cache=True)
    else:
        return view_activity_lite(template_id=template_id, term_number=latest_term)


def view_my_activitys(user_id, page, size, only_win, status, use_cache=False):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _MAX_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    activitys, count = get_user_activitys(user_id)
    a_list = []
    for activity in activitys:
        if status and not (status & activity.status):
            continue
        if only_win and activity.status < ACTIVITY_STATUS.ANNOUNCED:
            continue
        detail = create_activity_detail(user_id, activity, use_cache=use_cache)
        if only_win and detail['revealed']['winner']['uid'] != user_id:
            continue
        a_list.append(detail)

    start_index = offset
    if limit == 0:
        r_list = a_list[offset:]
    else:
        r_list = a_list[offset:offset + limit]

    return r_list, len(a_list)


def view_my_activitys_v2(user_id, page, size, only_win, status):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _MAX_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    activitys, count = get_user_activitys(
        user_id, only_win, status, limit, offset)
    a_list = []
    for activity in activitys:
        if only_win and activity.status < ACTIVITY_STATUS.ANNOUNCED:
            continue
        lite = create_activity_lite(activity)
        if only_win and lite['winner']['uid'] != user_id:
            continue
        my_numbers = get_user_numbers(user_id, activity.id)
        lite.update({
            'my': {
                'num_count': len(my_numbers)
            }
        })
        # add order id and status
        if activity.status == ACTIVITY_STATUS.ANNOUNCED and lite['winner']['uid'] == user_id:
            win_item = get_activity_win(activity.id)
            order_id = win_item.order_id
            lucky_order = get_awarded_order(order_id) or get_order(order_id)
            lite['my'].update({
                'order_id': order_id,
                'order_id_str': str(order_id),
                'order_status': lucky_order.status,
                'equal_price': float(get_goods(activity.goods_id).price)
            })
        a_list.append(lite)

    return a_list, count


def view_other_activitys(user_id, page, size, only_win, status):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _MAX_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    activitys, count = get_user_activitys(user_id, only_win, status, limit, offset)
    a_list = []
    for activity in activitys:
        if only_win and activity.status < ACTIVITY_STATUS.ANNOUNCED:
            continue
        lite = create_activity_lite(activity)
        if only_win and lite['winner']['uid'] != user_id:
            continue
        my_numbers = get_user_numbers(user_id, activity.id)
        lite.update({
            'my': {
                'num_count': len(my_numbers),
            }
        })
        a_list.append(lite)

    return a_list, count


def _fill_active_code(template_id):
    active_code = 0
    if template_id in settings.SHOW_BANNED_TIDS:
        active_code |= 2
    return active_code


def create_activity_lite(activity):
    lite_obj = ActivityLite()
    lite_obj['id'] = activity.id
    lite_obj['gid'] = activity.template_id
    lite_obj['term'] = activity.term_number
    lite_obj['created_at'] = utc_to_local(
        activity.created_at).strftime('%Y-%m-%d %H:%M:%S')
    lite_obj['goods'] = {
        'name': activity.name,
        'short_title': activity.short_title or activity.name,
        'desc': activity.desc,
        'cover': activity.cover or activity.images.split(',')[0]
    }
    lite_obj['unit'] = activity.unit
    lite_obj['price'] = activity.price
    goods = get_goods(activity.goods_id)
    lite_obj['is_resell'] = 1 if int(activity.target_amount) >= 1000 and goods.shipping_type==0 else 0
    if lite_obj['is_resell']:
        lite_obj['resell_price_h'] = int(float(goods.price)*0.9*1000)
        lite_obj['resell_price_l'] = int(float(goods.price)*0.8*1000)
    lite_obj['buy_limit'] = activity.buy_limit
    lite_obj['status'] = activity.status
    lite_obj['target_amount'] = activity.target_amount
    lite_obj['current_amount'] = activity.current_amount
    if activity.status == ACTIVITY_STATUS.ANNOUNCE_READY:
        lite_obj['remain_ms'] = _query_announce_countdown(activity)
    lite_obj['lucky_number'] = activity.winner
    if activity.status == ACTIVITY_STATUS.ANNOUNCED:
        # get winner info from cache
        cached_winner = redis_cache.get_activity_winner(activity.id)
        if cached_winner:
            winner_info = json.loads(cached_winner)
            #account = get_account(winner_info.get('uid'), use_cache=True)
            lite_obj.update({
                'winner': {
                    'uid': winner_info.get('uid'),
                    'avatar': winner_info.get('avatar'),
                    'nick_name': winner_info.get('nick_name'),
                    'ip': winner_info.get('ip'),
                    'addr': winner_info.get('addr'),
                    'time': utc_to_local(activity.announced_at).strftime('%Y-%m-%d %H:%M:%S'),
                    'num_count': winner_info.get('num_count') or len(winner_info.get('numbers'))
                }
            })
        else:
            win = get_activity_win(activity.id)
            if win:
                info = {} if not win.announce_info else json.loads(
                    win.announce_info)
                if info.get('winner'):
                    winner_info = info['winner']
                    number_count = winner_info.get(
                        'num_count') or len(winner_info.get('numbers'))
                    account = get_account(winner_info.get('uid'), use_cache=True)
                    lite_obj.update({
                        'winner': {
                            'uid': winner_info.get('uid'),
                            'avatar': account.avatar_id,
                            'nick_name': account.nick_name,
                            'ip': winner_info.get('ip'),
                            'addr': winner_info.get('addr'),
                            'time': utc_to_local(activity.announced_at).strftime('%Y-%m-%d %H:%M:%S'),
                            'num_count': number_count
                        }
                    })
                    # set winnner to cache
                    redis_cache.set_activity_winner(
                        activity.id, json.dumps(lite_obj['winner'], ensure_ascii=False))
                else:
                    lucky_user = get_account(win.winner, use_cache=True)
                    lite_obj.update({
                        'winner': {
                            'uid': lucky_user.id,
                            'avatar': lucky_user.avatar_id,
                            'nick_name': lucky_user.nick_name,
                        }
                    })
    lite_obj['active_code'] = _fill_active_code(activity.template_id)
    lite_obj['pk'] = activity.pk

    return lite_obj


def view_activitys(page, size, sort_id, unit=None, status=None):
    """
    查看夺宝list
    """
    lite_list = []
    limit = _DEFAULT_PAGE_SIZE if not size or size > _MAX_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    if not sort_id:
        activitys = []
        count = 0
        if (status and status & ACTIVITY_STATUS.ANNOUNCE_READY and
            status & ACTIVITY_STATUS.ANNOUNCED):
            # query cache
            id_list = redis_cache.get_latest_announce(start=offset, num=limit)
            activitys = get_activitys_by_ids(id_list, need_fill=False)
            if len(activitys) < limit:
                _LOGGER.warn('view all activitys, miss cache, offset:%s, limit:%s',
                    offset, limit)
                activitys, count = get_all_activitys(
                    limit, offset, unit=unit, status=status)
        else:
            activitys, count = get_all_activitys(
                limit, offset, unit=unit, status=status)
    elif sort_id == 1:
        activitys, count = get_hot_activitys(
            limit, offset, unit=unit, status=status)
    elif sort_id == 2:
        activitys, count = get_latest_activitys(
            limit, offset, unit=unit, status=status)
    elif sort_id == 3:
        activitys, count = get_left_activitys(
            limit, offset, unit=unit, status=status)
    elif sort_id == 4:
        activitys, count = get_costly_activitys(
            limit, offset, cost_reverse=True, unit=unit, status=status)
    elif sort_id == 5:
        activitys, count = get_costly_activitys(
            limit, offset, cost_reverse=False, unit=unit, status=status)
    else:
        raise ParamError('sort id invalid')

    for activity in activitys:
        lite_obj = create_activity_lite(activity)
        lite_list.append(lite_obj)

    return lite_list, count


def view_activitys_by_tids(tids, page, size):
    lite_list = []
    limit = _DEFAULT_PAGE_SIZE if not size or size > _MAX_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    activitys = get_hot_activitys_by_tids(tids, limit, offset)

    for activity in activitys:
        lite_obj = create_activity_lite(activity)
        lite_list.append(lite_obj)

    return lite_list


def view_tids_by_aids(aids):
    """
    根据活动id列表返回对应的模板id列表
    """
    id_list = []
    try:
        id_list = get_tids_by_aids(aids)
    except Exception as e:
        _LOGGER.exception('get_tids_by_aids exception, %s', e)
    return id_list


def view_revealed_list(page, size, template_id, use_cache=False):
    revealed_list = []
    limit = _DEFAULT_PAGE_SIZE if not size or size > _MAX_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    revealed_activitys, count = get_revealed_activitys(
        limit, offset, template_id)
    for activity in revealed_activitys:
        revealed_dict = get_revealed(activity, use_cache=use_cache)
        revealed = Revealed()
        revealed.activity_id = activity.id
        revealed.target_amount = activity.target_amount
        revealed.term = activity.term_number
        revealed.name = activity.name
        revealed.pk = activity.pk
        revealed.lucky_number = revealed_dict['lucky_number']
        revealed.reveal_time = revealed_dict['reveal_time']
        revealed.winner = revealed_dict['winner']
        revealed_list.append(revealed)

    return revealed_list, count


def view_calc_record(activity_id):
    activity = get_activity(activity_id)
    if not activity_id:
        raise_with_traceback(ParamError('activity id invalid'))

    calc_record = CalcRecord()
    calc_record.lucky_number = activity.winner
    calc_record.reveal_time = utc_to_local(
        activity.announced_at).strftime('%Y-%m-%d %H:%M:%S')
    win = get_activity_win(activity_id)
    if not win:
        info = {} if not activity.extend else json.loads(activity.extend)
    else:
        info = {} if not win.announce_info else json.loads(win.announce_info)
    a_list = info.get('a_list') or []
    need_update = False
    for item in a_list:
        if 'name' not in item:
            uid = item['uid']
            account = get_account(uid, use_cache=True)
            item['name'] = account.nick_name
            need_update = True
    if need_update:
        update_activity_win(activity_id, info)
    calc_record.calc = {
        'result_a': info.get('result_a'),
        'result_b': int(info.get('result_b', 0)) or None,
        'lottery_phase': info.get('lottery_phase'),
        'lottery_reference': info.get('lottery_reference'),
        'a_list': a_list
    }
    return calc_record


def start_next_activity(user_id, template_id):
    # check status
    activity_template = get_template(template_id)
    if not activity_template or activity_template.status != TEMPLATE_STATUS.STARTED:
        _LOGGER.error(
            'start_next_activity fail. activity template not exists or not started')
        raise_with_traceback(
            DataError('activity template %s not started' % template_id))

    success = redis_cache.try_template_lock(template_id)
    if not success:
        raise_with_traceback(CacheError('activity has started by others!'))

    try:
        activity = ActivityStarter.start(
            template_id, activity_template.goods_id)
        # generate lucky numbers for activity
        lucky_numbers = range(1, activity.target_amount + 1)
        redis_cache.generate_numbers(activity.id, *lucky_numbers)
        if activity.pk:
            setup_pk_info(activity)
        new_activity_index(activity, activity_template.weight)
        if activity.target_amount > 20 and random.randint(1,100) < 10:
            rand_int = random.randint(1,5)
            time.sleep(rand_int)
            if activity.unit == 1:
                rand_int = random.randint(1, 5)
                try:
                    buy_one(activity.id, rand_int)
                except Exception as e:
                    _LOGGER.error('start next activity, buy one exception, %s', e)
        # event_handler.call_activity_expire(activity.id)
        return activity
    except Exception as e:
        _LOGGER.error('start next activity of (%s) error, %s' %
                      (template_id, e))
        redis_cache.release_template_lock(template_id)
        raise_with_traceback(e)

    return None
