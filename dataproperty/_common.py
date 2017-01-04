# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from decimal import Decimal
import itertools

import six

from ._typecode import Typecode


DEFAULT_FLOAT_TYPE = Decimal
DEFAULT_INF_VALUE = DEFAULT_FLOAT_TYPE("inf")
DEFAULT_NAN_VALUE = DEFAULT_FLOAT_TYPE("nan")
DEFAULT_TYPE_VALUE_MAPPING = {
    Typecode.NONE: None,
    Typecode.INFINITY: DEFAULT_INF_VALUE,
    Typecode.NAN: DEFAULT_NAN_VALUE,
}
DEFAULT_CONST_VALUE_MAPPING = {
    True: True,
    False: False,
}

DEFAULT_STRICT_TYPE_MAPPING = {
    Typecode.NONE: False,
    Typecode.INTEGER: False,
    Typecode.FLOAT: False,
    Typecode.STRING: False,
    Typecode.DATETIME: True,
    Typecode.INFINITY: False,
    Typecode.NAN: False,
    Typecode.BOOL: False,
    Typecode.DICTIONARY: True,
}
STRICT_TYPE_MAPPING = dict(itertools.product(Typecode.LIST, [True]))
NOT_STRICT_TYPE_MAPPING = dict(itertools.product(Typecode.LIST, [False]))


def default_datetime_formatter(value):
    return six.text_type(value)
