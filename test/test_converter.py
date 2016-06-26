# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import datetime
from dateutil.tz import tzoffset
import pytest
import six

from dataproperty import TypeConversionError
from dataproperty import is_nan
from dataproperty.converter._core import NoneConverter
from dataproperty.converter._core import IntegerConverter
from dataproperty.converter._core import FloatConverter
from dataproperty.converter._core import DateTimeConverter


nan = float("nan")
inf = float("inf")


class Test_NoneConverter_convert:

    @pytest.mark.parametrize(["value", "expected"], [
        [None, None],
        [0, 0],
        [six.MAXSIZE, six.MAXSIZE],
        [False, False],
        ["test_string", "test_string"],
    ])
    def test_normal(self, value, expected):
        assert NoneConverter(value).convert() == expected


class Test_IntegerConverter_convert:

    @pytest.mark.parametrize(["value", "expected"], [
        [six.MAXSIZE, six.MAXSIZE], [-six.MAXSIZE, -six.MAXSIZE],
        [0., 0], [0.1, 0], [.5, 0],
        [True, 1], [False, 0],
        [str(six.MAXSIZE), six.MAXSIZE],
        [str(-six.MAXSIZE), -six.MAXSIZE],
    ])
    def test_normal(self, value, expected):
        assert IntegerConverter(value).convert() == expected

    @pytest.mark.parametrize(["value", "expected"], [
        ["", TypeConversionError],
        [None, TypeConversionError],
        ["test", TypeConversionError],
        ["0.0", TypeConversionError],
        ["0.1", TypeConversionError],
        ["-0.1", TypeConversionError],
        ["1e-05", TypeConversionError],
        [inf, TypeConversionError],
    ])
    def test_exception(self, value, expected):
        with pytest.raises(expected):
            IntegerConverter(value).convert()


class Test_FloatConverter_convert:

    @pytest.mark.parametrize(["value", "expected"], [
        [0.0, 0.0],
        [0.1, 0.1],
        [-0.1, -0.1],
        [1, 1.0],
        [-1, -1.0],
        ["0.0", 0.0],
        ["0.1", 0.1],
        ["-0.1", -0.1],
        ["1", 1.0],
        ["-1", -1.0],
        [.5, .5],
        [0., 0.0],
        ["1e-05", 1e-05],
        [inf, inf],
        [True, 1.0],
    ])
    def test_normal(self, value, expected):
        assert FloatConverter(value).convert() == expected

    @pytest.mark.parametrize(["value", "expected"], [
        ["", TypeConversionError],
        [None, TypeConversionError],
        ["test", TypeConversionError],
    ])
    def test_exception(self, value, expected):
        with pytest.raises(expected):
            FloatConverter(value).convert()


class Test_DateTimeConverter_convert:

    @pytest.mark.parametrize(["value", "expected"], [
        [
            datetime.datetime(
                2017, 3, 22, 10, 0, tzinfo=tzoffset(None, 32400)),
            datetime.datetime(
                2017, 3, 22, 10, 0, tzinfo=tzoffset(None, 32400)),
        ],
        [
            "2017-03-22T10:00:00+0900",
            datetime.datetime(2017, 3, 22, 10, 0, tzinfo=tzoffset(None, 32400))
        ],
    ])
    def test_normal(self, value, expected):
        dt_converter = DateTimeConverter(value)

        assert dt_converter.convert() == expected

    @pytest.mark.parametrize(["value", "expected"], [
        [
            "2015-03-08T00:00:00-0400",
            "2015-03-08 00:00:00-04:00",
        ],
        [
            "2015-03-08T12:00:00-0400",
            "2015-03-08 12:00:00-03:00",
        ],
        [
            "2015-03-08T00:00:00-0800",
            "2015-03-08 00:00:00-08:00",
        ],
        [
            "2015-03-08T12:00:00-0800",
            "2015-03-08 12:00:00-07:00",
        ],
    ])
    def test_normal_dst(self, value, expected):
        dt_converter = DateTimeConverter(value)

        assert str(dt_converter) == expected
        assert str(dt_converter.convert()) == expected

    @pytest.mark.parametrize(["value", "expected"], [
        ["invalid time string", TypeConversionError],
        [None, TypeConversionError],
        [11111, TypeConversionError],
    ])
    def test_exception(self, value, expected):
        dt_converter = DateTimeConverter(value)

        with pytest.raises(expected):
            dt_converter.convert()