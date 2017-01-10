'''
This library is provided to allow standard python logging
to output log data as JSON formatted strings
'''
import logging
import json
import datetime
import traceback

from inspect import istraceback


class JsonFormatter(logging.Formatter):

    def __init__(self, *args, **kwargs):
        """
        :param json_default: a function for encoding non-standard objects
            as outlined in http://docs.python.org/2/library/json.html
        :param json_encoder: optional custom encoder
        :param prefix: an optional string prefix added at the beginning of
            the formatted string
        """
        self.json_default = kwargs.pop("json_default", None)
        self.json_encoder = kwargs.pop("json_encoder", None)
        self.prefix = kwargs.pop('prefix', '')
        logging.Formatter.__init__(self, *args, **kwargs)
        if not self.json_encoder and not self.json_default:
            def _default_json_handler(obj):
                '''Prints dates in ISO format'''
                if isinstance(obj, datetime.datetime):
                    if obj.year < 1900:
                        # strftime do not work with date < 1900
                        return obj.isoformat()
                    return obj.strftime(self.datefmt or '%Y-%m-%dT%H:%M:%S.%f')
                elif isinstance(obj, datetime.date):
                    return obj.isoformat()
                elif isinstance(obj, datetime.time):
                    return obj.strftime('%H:%M')
                elif istraceback(obj):
                    tb = ''.join(traceback.format_tb(obj))
                    return tb.strip()
                elif isinstance(obj, Exception):
                    return "Exception: %s" % str(obj)
                return str(obj)
            self.json_default = _default_json_handler

    def jsonify_log_record(self, log_record):
        """Returns a json string of the log record."""
        log_record['@timestamp'] = datetime.datetime.utcnow()
        return json.dumps(log_record,
                          default=self.json_default,
                          cls=self.json_encoder)

    def format(self, record):
        return "%s%s" % (self.prefix, self.jsonify_log_record(record.msg))
