# -*- coding: utf-8
import json
import requests


TEMPLATE_ID = 208
GOODS_ID = 220

HEADERS = {
    'X-AUTH-USER': 1,
    'X-AUTH-TOKEN': '0878fc16-8e1f-45da-85af-f586daca8330'
}


def add_stock():
    api_path = 'http://120.26.57.89//admin/goods/%s' % GOODS_ID
    r = requests.get(api_path, headers=HEADERS)
    obj = json.loads(r.text)
    if obj['status'] != 0:
        print 'add stock error status:%s' % obj
    else:
        total = obj['data']['total']
        pay_load = {
            'total': total + 1
        }
        r = requests.put(api_path, data=json.dumps(pay_load), headers=HEADERS)
        obj = json.loads(r.text)
        if obj['status'] != 0:
            print 'error modify stock:%s' % obj
        else:
            print 'succ modify stock:%s' % GOODS_ID


def start():
    api_path = 'http://120.26.57.89/admin/activity/template/%s' % TEMPLATE_ID
    r = requests.get(api_path, headers=HEADERS)
    obj = json.loads(r.text)
    if obj['status'] != 0:
        print 'start error status:%s' % obj
    else:
        status = obj['data']['status']
        if status != 1:
            pay_load = {
                'status': 1
            }
            r = requests.put(api_path, data=json.dumps(pay_load), headers=HEADERS)
            obj = json.loads(r.text)
            if obj['status'] != 0:
                print 'error start:%s' % obj
            else:
                print 'succ start %s' % TEMPLATE_ID


if __name__ == "__main__":
    add_stock()
    start()
