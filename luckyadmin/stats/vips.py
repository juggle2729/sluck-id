# -*- coding: utf-8 -*-
import json
from datetime import datetime

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from luckycommon.db import missed_vips as db
from luckycommon.model.missed_vips import CALLBACK_STATUS
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import check_params
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.api import token_required
from luckycommon.utils.export import redirect_to_file, gen_filename


def get_callback_status_str(status):
    if status == 0:
        return u'未召回'
    status_str = []
    for k, v in CALLBACK_STATUS.to_dict().iteritems():
        if k & status > 0:
            status_str.append(v)
    return ','.join(status_str)


class MissedVipsView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        export = query_dct.pop('$export', None)
        if export:
            filename = gen_filename('missed_vips')
            header = ['uid', 'nick_name', 'phone', 'active_days',
                      'updated_time', 'lost_days', 'type', 'rank',
                      'recharge_amount', 'pay_count', 'win_count',
                      'win_amount', 'status', 'back_recharge', 'used_coupon']
            cn_header = [
                u'用户ID', u'用户昵称', u'联系电话', u'活跃天数', u'流失时间',
                u'流失天数', u'流失次数', u'用户排名', u'消费金额',
                u'参与活动次数', u'中奖次数', u'中奖金额', u'召回状态', u'召回后充值',
                u'心跳红包消费']
        items, total_count = db.list_missed_vips(query_dct)
        overview, back_info = db.calc_back_info(query_dct.get('created_at'))
        resp_items = []
        for item in items:
            data = item.as_dict()
            if item.uid in back_info:
                data['status'] |= CALLBACK_STATUS.BACK
                data['updated_time'] = utc_to_local_str(
                    back_info[item.uid]['updated_at'])
                data['back_recharge'] = back_info[item.uid]['recharge']
                data['used_coupon'] = back_info[item.uid]['used_coupon']
            data['status'] = get_callback_status_str(data['status'])
            data['updated_at'] = utc_to_local_str(data['updated_at'])

            if export:
                resp_items.append([data.get(x, '-') for x in header])
            else:
                resp_items.append(data)

        if export:
            return redirect_to_file(resp_items, cn_header, filename)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count,
                'overview': overview}

    def post(self, req):
        parmas_dct = json.loads(req.body)
        check_params(parmas_dct, ('ids', 'status'))
        db.batch_update_missed_vips(parmas_dct['ids'], parmas_dct['status'])

        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(MissedVipsView, self).dispatch(*args, **kwargs)


class BackVipsView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        export = query_dct.pop('$export', None)
        if export:
            filename = gen_filename('back_vips')
            header = ['call_at', 'calc_at', 'lost_days',
                      'total_count', 'back_count', 'back_rate',
                      'recharge_count', 'recharge_amount', 'recharge_rate',
                      'recharge_arpu', 'win_count', 'win_amount',
                      'win_rate', 'pay_count', 'coupon_amount']
            cn_header = [
                u'召回日期', u'统计日期', u'流失天数', u'总人数',
                u'召回人数', u'召回率', u'付费人数', u'付费金额', u'付费率',
                u'付费ARPU', u'中奖人数', u'中奖金额', u'中奖率', u'参加活动人数',
                u'红包消费金额']
        items, total_count = db.list_back_vips(query_dct)
        resp_items = []

        for item in items:
            data = item.as_dict()
            if data['total_count'] > 0:
                data['back_rate'] = float(
                    data['back_count']) / data['total_count']
            if data['back_count'] > 0:
                data['recharge_rate'] = float(data[
                    'recharge_count']) / data['back_count']
                data['win_rate'] = float(
                    data['win_count']) / data['back_count']
            if data['recharge_count'] > 0:
                delta = datetime.strptime(data['calc_at'], '%Y-%m-%d') -\
                    datetime.strptime(data['call_at'], '%Y-%m-%d')
                data['recharge_arpu'] = round(float(data['recharge_amount']) /
                                              data['recharge_count'] /
                                              delta.days, 2)

            if export:
                resp_items.append([data.get(x, '-') for x in header])
            else:
                resp_items.append(data)

        if export:
            return redirect_to_file(resp_items, cn_header, filename)
        else:
            return {'list': resp_items, 'page': query_dct.get('$page', 1),
                    'size': len(resp_items), 'total_count': total_count}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(BackVipsView, self).dispatch(*args, **kwargs)
