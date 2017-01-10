# -*- coding: utf-8 -*-
import json
import requests

API_URL = 'http://121.41.6.238/api/v1/regions/?area_id=%s'

def crawl(area_id=0, level=0):
    code = str(area_id)[:2]
    if code in ['11', '12', '31', '50'] and level > 2: 
        return
    if level > 3:
        return
    suojin = '\t'*level
    headers = {
        'X-AUTH-USER': 27,
        'X-AUTH-TOKEN': 'e8e65952-f719-4006-91c3-5f0d1c7f120d' 
    }
    api_url = API_URL % area_id
    try:
        r = requests.get(api_url, headers=headers)
        r_obj = json.loads(r.text)
        regions = r_obj['data']['regions']
        for region in regions:
            print '%s%s, %s, %s' % (suojin, region['id'], region['parent_id'], region['name'])
            crawl(region['id'], level+1)
    except Exception as e:
        print 'exception in crawl, %s' % e


if __name__ == "__main__":
    crawl()
