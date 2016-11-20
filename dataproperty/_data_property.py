# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import math
import itertools

from ._align_getter import align_getter
from ._container import MinMaxContainer
from ._error import TypeConversionError
from ._interface import DataPeropertyInterface
from ._factory import (
    NoneTypeFactory,
    StringTypeFactory,
    IntegerTypeFactory,
    FloatTypeFactory,
    BoolTypeFactory,
    DateTimeTypeFactory,
    InfinityTypeFactory,
    NanTypeFactory,
    DictionaryTypeFactory
)
from ._function import (
    get_number_of_digit,
    get_ascii_char_width,
    to_unicode
)
from ._typecode import Typecode
from ._type_checker import NanChecker
from ._type import FloatType


DEFAULT_IS_STRICT_TYPE_MAPPING = {
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


def default_bool_converter(value):
    return value


def default_datetime_converter(value):
    return value


class DataPeropertyBase(DataPeropertyInterface):
    __slots__ = ("__datetime_format_str")

    @property
    def typename(self):
        return Typecode.get_typename(self.typecode)

    @property
    def format_str(self):
        format_str = {
            Typecode.NONE: "",
            Typecode.INTEGER: "d",
            Typecode.BOOL: "",
            Typecode.DATETIME: self.__datetime_format_str,
            Typecode.DICTIONARY: "",
        }.get(self.typecode)

        if format_str is not None:
            return format_str

        if self.typecode in (Typecode.FLOAT, Typecode.INFINITY, Typecode.NAN):
            if NanChecker(self.decimal_places).is_type():
                return "f"

            return ".{:d}f".format(self.decimal_places)

        return "s"

    def __init__(self, datetime_format_str):
        self.__datetime_format_str = datetime_format_str


class DataProperty(DataPeropertyBase):
    __slots__ = (
        "__data",
        "__typecode",
        "__align",
        "__integer_digits",
        "__decimal_places",
        "__additional_format_len",
        "__str_len",
        "__ascii_char_width",
    )

    __type_factory_class_list = [
        NoneTypeFactory,
        IntegerTypeFactory,
        InfinityTypeFactory,
        NanTypeFactory,
        FloatTypeFactory,
        BoolTypeFactory,
        DictionaryTypeFactory,
        DateTimeTypeFactory,
        StringTypeFactory,
    ]

    @property
    def align(self):
        return self.__align

    @property
    def decimal_places(self):
        """
        :return:
            Decimal places if the ``data`` is ``float``.
            Returns ``0`` if the ``data`` is ``int``.
            Otherwise, returns ``float("nan")``.
        :rtype: int
        """

        return self.__decimal_places

    @property
    def typecode(self):
        """
        Return the type code that corresponds to the type of the ``data``.

        :return:
            One of the constants that are defined in the ``Typecode`` class.
        :rtype: int
        """

        return self.__typecode

    @property
    def data(self):
        """
        :return: Original data.
        :rtype: Original data type.
        """

        return self.__data

    @property
    def str_len(self):
        """
        :return: Length of the ``data`` as a string.
        :rtype: int
        """

        return self.__str_len

    @property
    def ascii_char_width(self):
        return self.__ascii_char_width

    @property
    def integer_digits(self):
        """
        :return:
            Integer digits if the ``data`` is ``int``/``float``.
            Otherwise, returns ``float("nan")``.
        :rtype: int
        """

        return self.__integer_digits

    @property
    def additional_format_len(self):
        return self.__additional_format_len

    def __init__(
            self, data,
            none_value=None, inf_value=float("inf"), nan_value=float("nan"),
            bool_converter=default_bool_converter,
            datetime_converter=default_datetime_converter,
            datetime_format_str="%Y-%m-%dT%H:%M:%S%z",
            is_strict_type_mapping=DEFAULT_IS_STRICT_TYPE_MAPPING,
            replace_tabs_with_spaces=True, tab_length=2):
        super(DataProperty, self).__init__(datetime_format_str)

        self.__set_data(
            data, none_value, inf_value, nan_value, is_strict_type_mapping)
        self.__convert_data(bool_converter, datetime_converter)
        self.__replace_tabs(replace_tabs_with_spaces, tab_length)
        self.__align = align_getter.get_align_from_typecode(self.typecode)

        try:
            integer_digits, decimal_places = get_number_of_digit(data)
        except OverflowError:
            integer_digits = float("nan")
            decimal_places = float("nan")
        self.__integer_digits = integer_digits
        self.__decimal_places = decimal_places
        self.__additional_format_len = self.__get_additional_format_len()
        self.__calc_length()

    def __repr__(self):
        element_list = []

        if self.typecode == Typecode.DATETIME:
            element_list.append(
                u"data={:s}".format(str(self.data)))
        else:
            try:
                element_list.append(
                    (u"data={:" + self.format_str + u"}").format(self.data))
            except UnicodeEncodeError:
                element_list.append(
                    (u"data={}").format(to_unicode(self.data)))
        element_list.extend([
            u"typename={:s}".format(self.typename),
            u"align={}".format(self.align),
            u"str_len={:d}".format(self.str_len),
            u"ascii_char_width={:d}".format(self.ascii_char_width),
            u"integer_digits={}".format(self.integer_digits),
            u"decimal_places={}".format(self.decimal_places),
            u"additional_format_len={:d}".format(self.additional_format_len),
        ])

        return u", ".join(element_list)

    def __get_additional_format_len(self):
        if not FloatType(self.data).is_type():
            return 0

        format_len = 0

        if float(self.data) < 0:
            # for minus character
            format_len += 1

        return format_len

    def __get_base_float_len(self):
        if any([self.integer_digits < 0, self.decimal_places < 0]):
            raise ValueError()

        float_len = self.integer_digits + self.decimal_places
        if self.decimal_places > 0:
            # for dot
            float_len += 1

        return float_len

    def __calc_length(self):
        if self.typecode == Typecode.INTEGER:
            self.__str_len = self.integer_digits + self.additional_format_len
            self.__ascii_char_width = self.__str_len
            return

        if self.typecode == Typecode.FLOAT:
            self.__str_len = (
                self.__get_base_float_len() + self.additional_format_len)
            self.__ascii_char_width = self.__str_len
            return

        if self.typecode == Typecode.DATETIME:
            full_format_str = "{:" + self.format_str + "}"

            try:
                self.__str_len = len(full_format_str.format(self.data))
            except ValueError:
                # reach to this line if the year <1900.
                # the datetime strftime() methods require year >= 1900.
                self.__str_len = len(str(self.data))

            self.__ascii_char_width = self.__str_len
            return

        unicode_str = to_unicode(self.data)
        self.__str_len = len(unicode_str)
        self.__ascii_char_width = get_ascii_char_width(unicode_str)

    def __set_data(
            self, data, none_value, inf_value, nan_value, is_strict_type_mapping):
        special_value_table = {
            Typecode.NONE: none_value,
            Typecode.INFINITY: inf_value,
            Typecode.NAN: nan_value,
        }

        for type_factory_class in self.__type_factory_class_list:
            is_strict = is_strict_type_mapping.get(type_factory_class(
                None, None).create_type_checker().typecode, False)
            type_factory = type_factory_class(data, is_strict)
            checker = type_factory.create_type_checker()

            if not checker.is_type():
                continue

            self.__typecode = checker.typecode

            special_value = special_value_table.get(self.__typecode)
            if special_value is not None:
                self.__data = special_value
                return

            self.__data = type_factory.create_type_converter().convert()

            return

        raise TypeConversionError("failed to convert: " + self.typename)

    def __convert_data(self, bool_converter, datetime_converter):
        if self.typecode == Typecode.BOOL:
            self.__data = bool_converter(self.__data)
        elif self.typecode == Typecode.DATETIME:
            self.__data = datetime_converter(self.__data)

    def __replace_tabs(self, replace_tabs_with_spaces, tab_length):
        if not replace_tabs_with_spaces:
            return

        try:
            self.__data = self.__data.replace("\t", " " * tab_length)
        except (TypeError, AttributeError):
            pass


class ColumnDataProperty(DataPeropertyBase):
    __slots__ = (
        "__typecode_bitmap",
        "__str_len",
        "__minmax_integer_digits",
        "__minmax_decimal_places",
        "__minmax_additional_format_len",
        "__data_prop_list",
    )

    __FACTORY_TABLE = {
        Typecode.NONE: NoneTypeFactory,
        Typecode.STRING: StringTypeFactory,
        Typecode.INTEGER: IntegerTypeFactory,
        Typecode.INFINITY: InfinityTypeFactory,
        Typecode.NAN: NanTypeFactory,
        Typecode.FLOAT: FloatTypeFactory,
        Typecode.BOOL: BoolTypeFactory,
        Typecode.DATETIME: DateTimeTypeFactory,
    }

    @property
    def align(self):
        return align_getter.get_align_from_typecode(self.typecode)

    @property
    def decimal_places(self):
        try:
            avg = self.minmax_decimal_places.mean()
        except TypeError:
            return float("nan")

        if NanChecker(avg).is_type():
            return float("nan")

        return int(math.ceil(avg))

    @property
    def typecode(self):
        return self.__get_typecode_from_bitmap()

    @property
    def padding_len(self):
        if self.typecode != Typecode.FLOAT:
            return self.__str_len

        max_len = self.__str_len
        col_format_str = "{:" + self.format_str + "}"

        for data_prop in self.__data_prop_list:
            if data_prop.typecode in [Typecode.INFINITY, Typecode.NAN]:
                continue

            try:
                formatted_value = col_format_str.format(data_prop.data)
            except (TypeError, ValueError):
                continue

            max_len = max(max_len, len(formatted_value))

        return max_len

    @property
    def minmax_integer_digits(self):
        return self.__minmax_integer_digits

    @property
    def minmax_decimal_places(self):
        return self.__minmax_decimal_places

    @property
    def minmax_additional_format_len(self):
        return self.__minmax_additional_format_len

    @property
    def type_factory(self):
        return self.__FACTORY_TABLE.get(self.typecode)

    def __init__(
            self,
            min_padding_len=0,
            datetime_format_str="%Y-%m-%dT%H:%M:%S%z"):
        super(ColumnDataProperty, self).__init__(datetime_format_str)

        self.__typecode_bitmap = Typecode.NONE
        self.__str_len = min_padding_len
        self.__minmax_integer_digits = MinMaxContainer()
        self.__minmax_decimal_places = MinMaxContainer()
        self.__minmax_additional_format_len = MinMaxContainer()
        self.__data_prop_list = []

    def __repr__(self):
        return ", ".join([
            "typename=" + self.typename,
            "align=" + str(self.align),
            "padding_len=" + str(self.padding_len),
            "integer_digits=({:s})".format(str(self.minmax_integer_digits)),
            "decimal_places=({:s})".format(str(self.minmax_decimal_places)),
            "additional_format_len=({:s})".format(
                str(self.minmax_additional_format_len)),
        ])

    def update_header(self, dataprop):
        self.__str_len = max(self.__str_len, dataprop.str_len)

    def update_body(self, dataprop):
        self.__typecode_bitmap |= dataprop.typecode
        self.__str_len = max(self.__str_len, dataprop.str_len)

        if dataprop.typecode in (Typecode.FLOAT, Typecode.INTEGER):
            self.__minmax_integer_digits.update(dataprop.integer_digits)
            self.__minmax_decimal_places.update(dataprop.decimal_places)

        self.__minmax_additional_format_len.update(
            dataprop.additional_format_len)

        self.__data_prop_list.append(dataprop)

    def __is_not_single_typecode(self, typecode):
        return all([
            self.__typecode_bitmap & typecode,
            self.__typecode_bitmap & ~typecode,
        ])

    def __is_float_typecode(self):
        number_typecode = (
            Typecode.INTEGER | Typecode.FLOAT | Typecode.INFINITY | Typecode.NAN)

        if self.__is_not_single_typecode(number_typecode):
            return False

        if bin(self.__typecode_bitmap & number_typecode).count("1") >= 2:
            return True

        return False

    def __get_typecode_from_bitmap(self):
        if self.__is_float_typecode():
            return Typecode.FLOAT

        if any([
            self.__is_not_single_typecode(Typecode.BOOL),
            self.__is_not_single_typecode(Typecode.DATETIME),
        ]):
            return Typecode.STRING

        typecode_list = [
            Typecode.STRING,
            Typecode.FLOAT,
            Typecode.INTEGER,
            Typecode.DATETIME,
            Typecode.BOOL,
            Typecode.INFINITY,
            Typecode.NAN,
        ]

        for typecode in typecode_list:
            if self.__typecode_bitmap & typecode:
                return typecode

        if self.__typecode_bitmap == Typecode.NONE:
            return Typecode.NONE

        return Typecode.STRING
