# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import pytest

from dataproperty import *


@pytest.fixture
def prop_extractor():
    return PropertyExtractor()


class Test_PropertyExtractor_extract_data_property_matrix:

    @pytest.mark.parametrize(["value", "non_value"], [
        [
            [
                [None, 1],
                [1.1, "a"],
            ],
            "null",
        ],
    ])
    def test_normal(self, prop_extractor, value, non_value):
        prop_extractor.data_matrix = value
        prop_extractor.none_value = non_value
        prop_matrix = prop_extractor.extract_data_property_matrix()

        assert len(prop_matrix) == 2

        prop = prop_matrix[0][0]
        assert prop.data == "null"
        assert prop.typecode == Typecode.NONE
        assert prop.align.align_code == Align.LEFT.align_code
        assert prop.align.align_string == Align.LEFT.align_string
        assert prop.str_len == 4
        assert is_nan(prop.decimal_places)
        assert prop.format_str == "s"

        prop = prop_matrix[0][1]
        assert prop.typecode == Typecode.INT
        assert prop.align.align_code == Align.RIGHT.align_code
        assert prop.align.align_string == Align.RIGHT.align_string
        assert prop.str_len == 1
        assert prop.decimal_places == 0
        assert prop.format_str == "d"

        prop = prop_matrix[1][0]
        assert prop.typecode == Typecode.FLOAT
        assert prop.align.align_code == Align.RIGHT.align_code
        assert prop.align.align_string == Align.RIGHT.align_string
        assert prop.str_len == 3
        assert prop.decimal_places == 1
        assert prop.format_str == ".1f"

        prop = prop_matrix[1][1]
        assert prop.typecode == Typecode.STRING
        assert prop.align.align_code == Align.LEFT.align_code
        assert prop.align.align_string == Align.LEFT.align_string
        assert prop.str_len == 1
        assert is_nan(prop.decimal_places)
        assert prop.format_str == "s"

    @pytest.mark.parametrize(["value", "expected"], [
        [None, TypeError],
    ])
    def test_exception(self, prop_extractor, value, expected):
        with pytest.raises(expected):
            prop_extractor.extract_data_property_matrix(value)


class Test_PropertyExtractor_extract_column_property_list:
    TEST_DATA_MATRIX = [
        [1, 1.1, "aa",  1,   1],
        [2, 2.2, "bbb", 2.2, 2.2],
        [3, 3.33, "cccc", -3, "ccc"],
    ]

    @pytest.mark.parametrize(["header_list", "value"], [
        [
            ["i", "f", "s", "if", "mix"],
            TEST_DATA_MATRIX,
        ],
        [
            None,
            TEST_DATA_MATRIX,
        ],
        [
            [],
            TEST_DATA_MATRIX,
        ],
    ])
    def test_normal(self, prop_extractor, header_list, value):
        prop_extractor.header_list = header_list
        prop_extractor.data_matrix = value
        col_prop_list = prop_extractor.extract_column_property_list()

        assert len(col_prop_list) == 5

        prop = col_prop_list[0]
        assert prop.typecode == Typecode.INT
        assert prop.align.align_code == Align.RIGHT.align_code
        assert prop.align.align_string == Align.RIGHT.align_string
        assert prop.padding_len == 1
        assert is_nan(prop.decimal_places)
        assert prop.format_str == "d"

        prop = col_prop_list[1]
        assert prop.typecode == Typecode.FLOAT
        assert prop.align.align_code == Align.RIGHT.align_code
        assert prop.align.align_string == Align.RIGHT.align_string
        assert prop.padding_len == 4
        assert prop.decimal_places == 2
        assert prop.format_str == ".2f"

        prop = col_prop_list[2]
        assert prop.typecode == Typecode.STRING
        assert prop.align.align_code == Align.LEFT.align_code
        assert prop.align.align_string == Align.LEFT.align_string
        assert prop.padding_len == 4
        assert is_nan(prop.decimal_places)
        assert prop.format_str == "s"

        prop = col_prop_list[3]
        assert prop.typecode == Typecode.FLOAT
        assert prop.align.align_code == Align.RIGHT.align_code
        assert prop.align.align_string == Align.RIGHT.align_string
        assert prop.padding_len == 3
        assert prop.decimal_places == 1
        assert prop.format_str == ".1f"

        prop = col_prop_list[4]
        assert prop.typecode == Typecode.STRING
        assert prop.align.align_code == Align.LEFT.align_code
        assert prop.align.align_string == Align.LEFT.align_string
        assert prop.padding_len == 3
        assert prop.decimal_places == 1
        assert prop.format_str == "s"

    @pytest.mark.parametrize(["header_list", "value", "expected"], [
        [
            None,
            None,
            TypeError
        ],
        [
            ["i", "f", "s", "if", "mix"],
            None,
            TypeError
        ],
    ])
    def test_exception(self, prop_extractor, header_list, value, expected):
        with pytest.raises(expected):
            prop_extractor.header_list = header_list
            prop_extractor.data_matrix = value
            prop_extractor.extract_column_property_list()
