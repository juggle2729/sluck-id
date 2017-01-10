"""
luckyservice api model

Define api layer model, used to wrap object from/to client

"""

from future.utils import raise_with_traceback

from luckycommon.utils.exceptions import ParamError, DataError


class BaseModel(dict):
    structure = {}
    default_fields = {}
    required_fields = []

    def __getattr__(self, name):
        return self[name] if name in self else None

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

    def set_fromdict(self, d):
        for k, v in d.items():
            self[k] = v


def check_params(data, model):

    for field in model.required_fields:
        if field not in data:
            raise_with_traceback(ParamError('require %s' % field))

    for f, t in model.get('structure', {}).iteritems():
        if f in data:
            if not isinstance(data[f], t):
                try:
                    data[f] = t(data[f])
                except (ValueError, TypeError) as e:
                    raise_with_traceback(DataError(e))
        else:
            data[f] = model.default_fields.get(f)

    return data
