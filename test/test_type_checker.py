# encoding: utf-8


"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import datetime
import itertools

from dateutil.tz import tzoffset
import pytest
import six

import dataproperty._type_checker as tc
from dataproperty import Typecode


nan = float("nan")
inf = float("inf")


class Test_NoneTypeChecker:

    @pytest.mark.parametrize(["value", "is_convert", "expected"], [
        [None, True, True],
        [None, False, True],
    ] + list(
        itertools.product(
            ["None", True, False, 0, six.MAXSIZE, inf, nan],
            [True, False],
            [False]
        ))
    )
    def test_normal_true(self, value, is_convert, expected):
        type_checker = tc.NoneTypeChecker(value, is_convert)
        assert type_checker.is_type() == expected
        assert type_checker.typecode == Typecode.NONE


class Test_IntegerTypeChecker:

    @pytest.mark.parametrize(["value", "is_convert"], [
        [0, True], [0, False],
        ["0", True],
        [" 1 ", True],
        [six.MAXSIZE, True], [six.MAXSIZE, False],
        [-six.MAXSIZE, True], [-six.MAXSIZE, False],
        [str(six.MAXSIZE), True], [str(-six.MAXSIZE), True],
    ])
    def test_normal_true(self, value, is_convert):
        type_checker = tc.IntegerTypeChecker(value, is_convert)
        assert type_checker.is_type()
        assert type_checker.typecode == Typecode.INT

    @pytest.mark.parametrize(["value", "is_convert"], [
        ["", True], ["", False],
        [None, True], [None, False],
        [nan, True], [nan, False],
        [inf, True], [inf, False],
        [0.5, True], [0.5, False],
        ["0.5", True], ["0.5", False],
        [.999, True], [.999, False],
        [".999", True], [".999", False],
        ["test", True], ["test", False],
        ["1a1", True], ["1a1", False],
        ["11a", True], ["11a", False],
        ["a11", True], ["a11", False],
        [True, True], [True, False],
        [1e-05, True], [1e-05, False],
        [-1e-05, True], [-1e-05, False],
        ["1e-05", True], ["1e-05", False],
        ["-1e-05", True], ["-1e-05", False],
        [-0.00001, True], [-0.00001, False],
        ["0", False],
        ["0xff", True], ["0xff", False],

        [" 1 ", False],
        [str(six.MAXSIZE), False], [str(-six.MAXSIZE), False],
    ])
    def test_normal_false(self, value, is_convert):
        assert not tc.IntegerTypeChecker(value, is_convert).is_type()


class Test_FloatTypeChecker:

    @pytest.mark.parametrize(["value", "is_convert"], [
        [0.0, True], [0.0, False],
        [0.1, True], [0.1, False],
        [-0.1, True], [-0.1, False],
        [1, True],
        [-1, True],
        ["0.0", True],
        ["0.1", True],
        ["-0.1", True],
        ["1", True],
        ["-1", True],
        [.5, True], [.5, False],
        [0., True], [0., False],
        ["1e-05", True],
        [nan, True], [nan, False],
        [inf, True], [inf, False],
        [six.MAXSIZE, True], [-six.MAXSIZE, True],
        [str(six.MAXSIZE), True], [str(-six.MAXSIZE), True],
    ])
    def test_normal_true(self, value, is_convert):
        type_checker = tc.FloatTypeChecker(value, is_convert)
        assert type_checker.is_type()
        assert type_checker.typecode == Typecode.FLOAT

    @pytest.mark.parametrize(["value", "is_convert"], [
        [1, False],
        [-1, False],
        ["0.1", False],
        ["0.0", False],
        ["-0.1", False],
        ["-1", False],
        ["1", False],
        ["1e-05", False],
        ["", True], ["", False],
        [None, True], [None, False],
        ["test", True], ["test", False],
        ["inf", True], ["inf", False],
        [True, True], [True, False],
        [six.MAXSIZE, False], [-six.MAXSIZE, False],
        [str(six.MAXSIZE), False], [str(-six.MAXSIZE), False],
    ])
    def test_normal_false(self, value, is_convert):
        assert not tc.FloatTypeChecker(value, is_convert).is_type()


class Test_DateTimeTypeChecker:

    @pytest.mark.parametrize(["value", "is_convert"], [
        [
            datetime.datetime(
                2017, 3, 22, 10, 0, tzinfo=tzoffset(None, 32400)),
            True,
        ],
        [
            datetime.datetime(
                2017, 3, 22, 10, 0, tzinfo=tzoffset(None, 32400)),
            False,
        ],
        [
            "2017-03-22T10:00:00+0900",
            True,
        ],
    ])
    def test_normal_true(self, value, is_convert):
        type_checker = tc.DateTimeTypeChecker(value, is_convert)
        assert type_checker.is_type()
        assert type_checker.typecode == Typecode.DATETIME

    @pytest.mark.parametrize(["value", "is_convert"], [
        ["2017-03-22T10:00:00+0900", False],
        ["invalid time string", True],
        ["invalid time string", False],
        [None, True],
        [None, False],
        [six.MAXSIZE, True], [six.MAXSIZE, False],
    ])
    def test_normal_false(self, value, is_convert):
        assert not tc.DateTimeTypeChecker(value, is_convert).is_type()


class Test_InfinityChecker:

    @pytest.mark.parametrize(
        ["value", "is_convert", "expected"],
        list(itertools.product(
            [0.0, six.MAXSIZE, "0", nan],
            [True, False],
            [False]
        )) + list(itertools.product(
            [inf],
            [True, False],
            [True]
        )) + [
            ["inf", True, True],
            ["inf", False, False],
            ["INF", True, True],
            ["INF", False, False],
        ]
    )
    def test_normal_true(self, value, is_convert, expected):
        type_checker = tc.InfinityChecker(value, is_convert)
        assert type_checker.is_type() == expected
        assert type_checker.typecode == Typecode.INFINITY
