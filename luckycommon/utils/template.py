# -*- coding: utf-8 -*-
import json

from django.template.loader import render_to_string
from django.conf import settings

from luckycommon.utils.api import EnhencedEncoder


def generate_from_template(template_name, data_dict=None, has_title=True, country=None, command=None):
    if not data_dict:
        data_dict = {}
    if not template_name.endswith('html'):
        template_name += '.html'
    if not country:
        country = settings.COUNTRY
    template_name = '%s/%s' % (country, template_name)

    rendered = render_to_string(template_name, data_dict)
    if has_title:
        title, content = rendered.split('\n', 1)

        resp = {
            'title': title,
            'content': content,
            'command': command
        }
        return json.dumps(resp, cls=EnhencedEncoder, ensure_ascii=False)
    else:
        return rendered.encode('utf-8')
