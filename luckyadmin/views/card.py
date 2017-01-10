# -*- coding: utf-8 -*-
import logging

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
import xlrd

from luckycommon.order.db import red_envelope as db
from luckycommon.order.db.charge_card import get_card_info
from luckycommon.order.model.order import ORDER_STATUS, RED_ENVELOPE_STATUS
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import utc_to_local_str
from luckycommon.utils.export import redirect_to_file, gen_filename

_LOGGER = logging.getLogger(__name__)


class RedEnvelopeView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        export = query_dct.pop('$export', None)
        resp_items = []

        if export:
            filename = gen_filename('red_envelope')
            header = [u'user_id', u'order_id', u'open_id', u'price', u'status',
                      u'order_status']

        # normal
        items, total_count = db.list_red_envelopes(query_dct)
        for item in items:
            red_envelope, order_status = item
            data = red_envelope.as_dict()
            data['order_id'] = str(data['order_id'])
            data['order_status'] = order_status
            data['updated_at'] = utc_to_local_str(data['updated_at'])
            data['created_at'] = utc_to_local_str(data['created_at'])
            if export:
                t = []
                for x in header:
                    v = data.get(x)
                    if v is None:
                        v = '-'
                    if x == 'status':
                        t.append(RED_ENVELOPE_STATUS.get_label(v))
                    elif x == 'order_status':
                        t.append(ORDER_STATUS.get_label(v))
                    elif x == 'order_id':
                        # NOTE: this is for bug of tablib
                        t.append(v + ' ')
                    else:
                        t.append(v)
                resp_items.append(t)
            else:
                resp_items.append(data)

        if export:
            return redirect_to_file(resp_items, header, filename)
        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        # batch ship from excel
        if 'excel_data' in req.FILES:
            data = req.FILES['excel_data']
            imported_data = []
            book = xlrd.open_workbook(file_contents=data.read())
            sh = book.sheet_by_index(0)
            for x in range(sh.nrows):
                imported_data.append(sh.row_values(x))
            db.manual_sent_redenvelops(imported_data, req.user_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(RedEnvelopeView, self).dispatch(*args, **kwargs)


@require_GET
@response_wrapper
@token_required
def get_charge_card(req, order_id):
    info = get_card_info(long(order_id))
    return info
