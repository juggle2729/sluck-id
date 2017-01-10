# -*- coding: utf-8 -*-

import json
import logging

from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator

from luckycommon.preset.db import preset as preset_db
from luckycommon.preset.db import loading as loading_db
from luckycommon.preset.db import discovery as discovery_db
from luckycommon.preset.db import banner as banner_db
from luckycommon.preset.db import shortcut as shortcut_db
from luckycommon.db.abtest import get_abtest
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)


class PresetView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = preset_db.list_preset(query_dct)

        resp_items = []
        for item in items:
            data = item.as_dict()
            data['created_at'] = utc_to_local_str(data['created_at'])
            data['updated_at'] = utc_to_local_str(data['updated_at'])
            data['content'] = json.loads(item.content or '{}')
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        param_dct = json.loads(req.body)
        preset_db.upsert_preset(base=param_dct.get('base'))
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(PresetView, self).dispatch(*args, **kwargs)


class SinglePresetView(TemplateView):

    def get(self, req, preset_id):
        preset = preset_db.get_preset(id=int(preset_id))
        data = preset.as_dict()
        data['created_at'] = utc_to_local_str(data['created_at'])
        data['updated_at'] = utc_to_local_str(data['updated_at'])
        data['content'] = json.loads(preset.content or '{}')
        return data

    def post(self, req, preset_id):
        return self.put(req, preset_id)

    def put(self, req, preset_id):
        query_dct = json.loads(smart_unicode(req.body))
        preset_db.upsert_preset(query_dct, int(preset_id))
        return {}

    def delete(self, req, preset_id):
        preset_db.delete_preset(int(preset_id))
        _LOGGER.info('delete preset: %s, user: %s', preset_id, req.user_id)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SinglePresetView, self).dispatch(*args, **kwargs)


class LoadingView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = loading_db.list_loading(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            data = item.as_dict()
            if item.abtest:
                data['abtest'] = get_abtest(item.abtest).name
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        param_dct = json.loads(req.body)
        loading_db.upsert_loading(param_dct)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(LoadingView, self).dispatch(*args, **kwargs)


class SingleLoadingView(TemplateView):

    def get(self, req, loading_id):
        loading = loading_db.get_loading(id=int(loading_id))
        loading.updated_at = utc_to_local_str(loading.updated_at)
        loading.created_at = utc_to_local_str(loading.created_at)
        return loading.as_dict()

    def put(self, req, loading_id):
        query_dct = json.loads(smart_unicode(req.body))
        loading_db.upsert_loading(query_dct, int(loading_id))
        return {}

    def delete(self, req, loading_id):
        loading_db.delete_loading(int(loading_id))
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleLoadingView, self).dispatch(*args, **kwargs)


class DiscoveryView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = discovery_db.list_discovery(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            data = item.as_dict()
            if item.abtest:
                data['abtest'] = get_abtest(item.abtest).name
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        param_dct = json.loads(req.body)
        discovery_db.upsert_discovery(param_dct)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(DiscoveryView, self).dispatch(*args, **kwargs)


class SingleDiscoveryView(TemplateView):

    def get(self, req, discovery_id):
        discovery = discovery_db.get_discovery(id=int(discovery_id))
        discovery.updated_at = utc_to_local_str(discovery.updated_at)
        discovery.created_at = utc_to_local_str(discovery.created_at)
        return discovery.as_dict()

    def post(self, req, discovery_id):
        return self.put(req, discovery_id)

    def put(self, req, discovery_id):
        query_dct = json.loads(smart_unicode(req.body))
        discovery_db.upsert_discovery(query_dct, int(discovery_id))
        return {}

    def delete(self, req, discovery_id):
        discovery_db.delete_discovery(int(discovery_id))
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleDiscoveryView, self).dispatch(*args, **kwargs)


class BannerView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = banner_db.list_banner(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            data = item.as_dict()
            if item.abtest:
                data['abtest'] = get_abtest(item.abtest).name
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        param_dct = json.loads(req.body)
        banner_db.upsert_banner(param_dct)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(BannerView, self).dispatch(*args, **kwargs)


class SingleBannerView(TemplateView):

    def get(self, req, banner_id):
        banner = banner_db.get_banner(id=int(banner_id))
        banner.updated_at = utc_to_local_str(banner.updated_at)
        banner.created_at = utc_to_local_str(banner.created_at)
        return banner.as_dict()

    def put(self, req, banner_id):
        query_dct = json.loads(smart_unicode(req.body))
        banner_db.upsert_banner(query_dct, int(banner_id))
        return {}

    def delete(self, req, banner_id):
        banner_db.delete_banner(int(banner_id))
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleBannerView, self).dispatch(*args, **kwargs)


class ShortcutView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = shortcut_db.list_shortcut(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            data = item.as_dict()
            if item.abtest:
                data['abtest'] = get_abtest(item.abtest).name
            resp_items.append(data)

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        param_dct = json.loads(req.body)
        shortcut_db.upsert_shortcut(param_dct)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(ShortcutView, self).dispatch(*args, **kwargs)


class SingleShortcutView(TemplateView):

    def get(self, req, shortcut_id):
        shortcut = shortcut_db.get_shortcut(id=int(shortcut_id))
        shortcut.updated_at = utc_to_local_str(shortcut.updated_at)
        shortcut.created_at = utc_to_local_str(shortcut.created_at)
        return shortcut.as_dict()

    def put(self, req, shortcut_id):
        query_dct = json.loads(smart_unicode(req.body))
        shortcut_db.upsert_shortcut(query_dct, int(shortcut_id))
        return {}

    def delete(self, req, shortcut_id):
        shortcut_db.delete_shortcut(int(shortcut_id))
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleShortcutView, self).dispatch(*args, **kwargs)
