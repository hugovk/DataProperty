#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import print_function

import datetime
import sys

from dataproperty import DataPropertyExtractor
from typepy import Typecode


def display_dp_matrix_attr(dp_matrix, attr_name):
    """
    show a value assocciated with an attribute for each
    DataProperty instance in the dp_matrix
    """

    print()
    print("---------- {:s} ----------".format(attr_name))
    for dp_list in dp_matrix:
        print([getattr(dp, attr_name) for dp in dp_list])


def main():
    # sample data definitions
    dt = datetime.datetime(2017, 1, 1, 0, 0, 0)
    inf = float("inf")
    nan = float("nan")

    # extract data property for each element from a matrix
    dp_extractor = DataPropertyExtractor()
    dp_extractor.data_matrix = [
        [1, 1.1,  "aa",   1,   1,     True,   inf,   nan,   dt],
        [2, 2.2,  "bbb",  2.2, 2.2,   False,  "inf", "nan", dt],
        [3, 3.33, "cccc", -3,  "ccc", "true", inf,
            "NAN", "2017-01-01T01:23:45+0900"],
    ]
    dp_matrix = dp_extractor.to_dataproperty_matrix()

    print("---------- typename ----------")
    for dp_list in dp_matrix:
        print([dp.typecode.name for dp in dp_list])

    display_dp_matrix_attr(dp_matrix, "data")
    display_dp_matrix_attr(dp_matrix, "align")
    display_dp_matrix_attr(dp_matrix, "length")
    display_dp_matrix_attr(dp_matrix, "integer_digits")
    display_dp_matrix_attr(dp_matrix, "decimal_places")

    return 0


if __name__ == "__main__":
    sys.exit(main())
