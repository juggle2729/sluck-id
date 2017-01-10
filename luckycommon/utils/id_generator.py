# -*- coding: utf-8 -*-
import uuid
import time
import logging
import itertools
import random
from datetime import datetime
from hashlib import md5

from django.conf import settings


LOGGER = logging.getLogger(__name__)


class IdComponent(object):

    def __init__(self, name, length):
        self.name = name
        self.length = length
        self.mask = (1 << length) - 1

    def get_mask(self):
        return self.mask

    def get_length(self):
        return self.length

    def generate_long(self):
        raise NotImplementedError('IdComponent is an Abstract Class')

    def generate_string(self):
        raise NotImplementedError('IdComponent is an Abstract Class')

    def __repr__(self):
        return '(%s,%s)' % (self.name, self.length)


class ZeroComponent(IdComponent):

    def __init__(self, length):
        super(ZeroComponent, self).__init__('unused', length)

    def generate_long(self):
        return 0L

    def generate_string(self):
        return '0' * self.get_length()


class SecondComponent(IdComponent):

    def __init__(self, length):
        super(SecondComponent, self).__init__('second', length)

    def generate_long(self):
        utc_now = datetime.utcnow()
        return long(time.mktime(utc_now.timetuple()))

    def generate_string(self):
        return str(self.generate_long()).zfill(self.length)


class MillisecondComponent(IdComponent):

    def __init__(self, length):
        super(MillisecondComponent, self).__init__('millisecond', length)

    def generate_long(self):
        utc_now = datetime.utcnow()
        return long(utc_now.microsecond / 1000)

    def generate_string(self):
        return str(self.generate_long()).zfill(self.length)


class LocalSeqComponent(IdComponent):

    """
    Thread safe local counter
    """
    _COUNTER = itertools.count()

    def __init__(self, length):
        super(LocalSeqComponent, self).__init__('local_sequence', length)

    def generate_long(self):
        return long(LocalSeqComponent._COUNTER.next())

    def generate_string(self):
        return str(self.generate_long()).zfill(self.length)


class ConstantComponent(IdComponent):

    """
    generate constant value, used for tag instance
    instance_id must be long type while used for LongIdGenerator
    or be string type when for StringIdGenerator
    """

    def __init__(self, length, constant_id):
        super(ConstantComponent, self).__init__('instance_id', length)
        self.constant_id = constant_id

    def generate_long(self):
        return long(self.constant_id)

    def generate_string(self):
        return str(self.constant_id)


class LongIdGenerator(object):

    """
    generate long bit id by IdComponent
    """
    _DEFAULT_COMPONENTS = [ZeroComponent(3),
                           SecondComponent(31),
                           MillisecondComponent(10),
                           LocalSeqComponent(10),
                           ZeroComponent(10)]

    def __init__(self, instance_id=None):
        if not instance_id:
            self.rules = LongIdGenerator._DEFAULT_COMPONENTS
        else:
            self.rules = [ConstantComponent(10, instance_id),
                          SecondComponent(31),
                          MillisecondComponent(10),
                          LocalSeqComponent(10),
                          ZeroComponent(3)]
            instance_id = long(instance_id)
            if instance_id > self.rules[0].get_mask() or instance_id < 0:
                raise Exception('instance_id(%s) for LongIdGenerator invalid',
                                instance_id)

    def generate(self):
        id = 0L
        for component in self.rules:
            l = component.generate_long()
            id = (id << component.get_length()) + l

        return id


class StringIdGenerator(object):

    """
    generate string id by IdComponent
    """
    _DEFAULT_COMPONENTS = [ZeroComponent(9),
                           SecondComponent(10),
                           MillisecondComponent(3),
                           LocalSeqComponent(10)]

    def __init__(self, instance_id=None):
        if not instance_id:
            self.rules = StringIdGenerator._DEFAULT_COMPONENTS
        else:
            self.rules = [ConstantComponent(9, instance_id),
                          SecondComponent(10),
                          MillisecondComponent(3),
                          LocalSeqComponent(10)]
            instance_id = str(instance_id)
            if len(instance_id) > self.rules[0].get_length():
                instance_id = instance_id[:self.rules[0].get_length()]

    def generate(self):
        string = ''
        for component in self.rules:
            string += component.generate_string()

        return string


class UUidGenerator(object):

    """
    generate uuid by name or random
    """
    _NAME_SPACE = 'lucky-service'

    @staticmethod
    def generate(name=None):
        if name:
            namespace = uuid.UUID(md5(UUidGenerator._NAME_SPACE).hexdigest())
            return str(uuid.uuid3(namespace, name.encode('utf-8')))
        else:
            return str(uuid.uuid4())


_LONG_ID_GENERATOR_DICT = {
    """
    10X: 1 means type, X means service instance id,
         when scaling to multiple service, X will be incremented.
    """
    'activity': LongIdGenerator(instance_id=100+settings.SERVICE_ID),
    'order': LongIdGenerator(instance_id=200+settings.SERVICE_ID),
    'transaction': LongIdGenerator(instance_id=300+settings.SERVICE_ID),
    'pay': LongIdGenerator(instance_id=400+settings.SERVICE_ID),
}

_STRING_ID_GENERATOR_DICT = {
    'activity': StringIdGenerator(instance_id='%dactivity' % settings.SERVICE_ID),
    'order': StringIdGenerator(instance_id='%dorder' % settings.SERVICE_ID),
    'transaction': StringIdGenerator(instance_id='%dtransaction' % settings.SERVICE_ID),
    'pay': StringIdGenerator(instance_id='%dpay' % settings.SERVICE_ID)
}


# public method

def generate_long_id(name=None):
    generator = _LONG_ID_GENERATOR_DICT.get(name)
    if not generator:
        generator = LongIdGenerator()
    return generator.generate()


def generate_string_id(name=None):
    generator = _STRING_ID_GENERATOR_DICT.get(name)
    if not generator:
        generator = StringIdGenerator()
    return generator.generate()


def generate_uuid(name=None):
    return UUidGenerator.generate(name)


def generate_auth_code(length=6):
    l = 10 ** (length - 1)
    h = 10 ** length
    return str(random.randrange(l, h))

if __name__ == "__main__":
    print '------test LongIdGenerator------'
    id_generator = LongIdGenerator(instance_id=101)
    for _ in xrange(10):
        print id_generator.generate()
    print '------test StringIdGenerator------'
    str_generator = StringIdGenerator(instance_id='AbcD')
    for _ in xrange(10):
        print str_generator.generate()
    print '------test UUidGenerator------'
    for _ in xrange(10):
        print UUidGenerator.generate()
