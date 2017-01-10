# -*- coding: utf-8 -*-

from enum import Enum


class CustomEnum(Enum):
    @classmethod
    def get_name(cls, value):
        for item in list(cls):
            if item.value == value:
                return item.name
        return None

    @classmethod
    def get_value(cls, name):
        for item in list(cls):
            if item.name == name:
                return item.value
        return None

    @classmethod
    def names(cls):
        return [item.name for item in list(cls)]

    @classmethod
    def values(cls):
        return [item.value for item in list(cls)]
