
import urllib2, urllib
from crypto import *
class HttpApi:
    def __init__(self, logger):
        self.logger = logger
        self.code = 0
        self.reason = ""
        self.crypto = CryptoHelper()

    def getStatus(self):
        return self.code, self.reason

    def httpPostCall(self, url, data, urlencode = True, headers = {}):
        if urlencode:
            encoded_data = urllib.urlencode(data)
        else:
            encoded_data = data
        self.logger.debug("Request:%s\nAdded HTTP HEAD=%s\n%s" %(url, headers, encoded_data))
        req = urllib2.Request(url, headers=headers)
        try:
            response = urllib2.urlopen(req, encoded_data)
            if response.getcode() != 200:
                self.code = response.getcode()
                self.logger.error("HTTP bad status:%d" %(response.getcode()))
                return None, None
        except urllib2.HTTPError, e:
            if hasattr(e, 'reason'):
                self.logger.error("HTTP error:%d %s" %(e.code, e.reason))
                self.reason = e.reason
            else:
                self.logger.error("HTTP error:%d" %(e.code))
            self.code = e.code
            return None, None
        except urllib2.URLError, e:
            self.logger.error("Url error: %s" %(e.reason))
            self.code = -1
            self.reason = e.reason
            return None, None
        except Exception, e:
            self.logger.error("Error:%s" %(str(e)))
            self.code = -2
            return None, None

        self.logger.debug("Get response:\n%s\n%s" %(response.getcode(), response.info()))
        data = response.read()
        self.logger.debug("Response data:%s\n" %(data))
        return response.info(), data
        
    def httpGetCall(self, url, data):
        req = url + "?" + urllib.urlencode(data)
        self.logger.debug("Request:%s" %(req))
        try:
            response = urllib2.urlopen(req)
            if response.getcode() != 200:
                self.logger.error("HTTP bad status:%d" %(response.getcode()))
                self.code = response.getcode()
                return None,None
        except urllib2.URLError, e:
            self.logger.error("Url error: %s" %(e.reason))
            self.code = -1
            self.reason = e.reason
            return None,None
        except urllib2.HTTPError, e:
            if hasattr(e, 'reason'):
                self.logger.error("HTTP error:%d %s" %(e.code, e.reason))
                self.reason = e.reason
            else:
                self.logger.error("HTTP error:%d" %(e.code))
            self.code = e.code
            return None,None
        except Exception, e:
            self.logger.error("Error:%s" %(str(e)))
            self.code = -2
            return None,None
        
        self.logger.debug("Get response:\n%d\n%s" %(response.getcode(), response.info()))
        data = response.read()
        self.logger.debug("Response data:%s\n" %(data))
        return response.info(), data

def decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = decode_list(item)
        elif isinstance(item, dict):
            item = decode_dict(item)
        rv.append(item)
    return rv

def decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = decode_list(value)
        elif isinstance(value, dict):
            value = decode_dict(value)
        rv[key] = value
    return rv

class OpException(Exception):
    def __init__(self, op, code, reason):
        self.op = op
        self.code = code
        self.reason = reason
    def __str__(self):
        return repr(self.value)
