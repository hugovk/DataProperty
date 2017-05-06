# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import division
from __future__ import unicode_literals

import abc

from typepy.type import RealNumber


class AbstractContainer(object):

    @abc.abstractproperty
    def min_value(self):  # pragma: no cover
        pass

    @abc.abstractproperty
    def max_value(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def mean(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def update(self, value):  # pragma: no cover
        pass

    def __repr__(self):
        return ", ".join([
            "min={}".format(self.min_value),
            "max={}".format(self.max_value),
        ])


class ListContainer(AbstractContainer):
    __slots__ = ("__value_list")

    @property
    def min_value(self):
        try:
            return min(self.__value_list)
        except ValueError:
            return None

    @property
    def max_value(self):
        try:
            return max(self.__value_list)
        except ValueError:
            return None

    @property
    def value_list(self):
        return self.__value_list

    def __init__(self, value_list=None):
        if value_list is None:
            self.__value_list = []
        else:
            self.__value_list = value_list

    def mean(self):
        try:
            return sum(self.__value_list) / len(self.__value_list)
        except ZeroDivisionError:
            return float("nan")

    def update(self, value):
        store_value = RealNumber(value).try_convert()
        if store_value is None:
            return

        self.__value_list.append(store_value)


class MinMaxContainer(AbstractContainer):
    __slots__ = ("__min_value", "__max_value")

    @property
    def min_value(self):
        return self.__min_value

    @property
    def max_value(self):
        return self.__max_value

    def __init__(self, value_list=None):
        self.__min_value = None
        self.__max_value = None

        if value_list is None:
            return

        for value in value_list:
            self.update(value)

    def __eq__(self, other):
        return all([
            self.min_value == other.min_value,
            self.max_value == other.max_value,
        ])

    def __ne__(self, other):
        return any([
            self.min_value != other.min_value,
            self.max_value != other.max_value,
        ])

    def __contains__(self, x):
        return self.min_value <= x <= self.max_value

    def diff(self):
        try:
            return self.max_value - self.min_value
        except TypeError:
            return float("nan")

    def mean(self):
        try:
            return (self.max_value + self.min_value) * 0.5
        except TypeError:
            return float("nan")

    def update(self, value):
        if value is None:
            return

        if self.__min_value is None:
            self.__min_value = value
        else:
            self.__min_value = min(self.__min_value, value)

        if self.__max_value is None:
            self.__max_value = value
        else:
            self.__max_value = max(self.__max_value, value)
