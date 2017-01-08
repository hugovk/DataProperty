# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from decimal import Decimal
import math

from mbstrdecoder import MultiByteStrDecoder
import six

from ._align_getter import align_getter
from ._common import DefaultValue
from ._container import (
    MinMaxContainer,
    ListContainer,
)
from ._error import TypeConversionError
from ._interface import DataPeropertyInterface
from ._function import (
    get_number_of_digit,
    get_ascii_char_width,
)
from ._type import (
    NoneType,
    StringType,
    NullStringType,
    IntegerType,
    FloatType,
    DateTimeType,
    BoolType,
    InfinityType,
    NanType,
    DictionaryType,
)
from ._typecode import Typecode
from ._type_checker import NanChecker


class DataPeropertyBase(DataPeropertyInterface):
    __slots__ = ("__datetime_format_str")

    @property
    def typename(self):
        return Typecode.get_typename(self.typecode)

    @property
    def format_str(self):
        format_str = {
            Typecode.NONE: "{}",
            Typecode.INTEGER: "{:d}",
            Typecode.BOOL: "{}",
            Typecode.DATETIME: "{:" + self.__datetime_format_str + "}",
            Typecode.DICTIONARY: "{}",
        }.get(self.typecode)

        if format_str is not None:
            return format_str

        if self.typecode in (Typecode.FLOAT, Typecode.INFINITY, Typecode.NAN):
            if NanChecker(self.decimal_places).is_type():
                return "{:f}"

            return "{:" + ".{:d}f".format(self.decimal_places) + "}"

        return "{:s}"

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

    __type_class_list = [
        NoneType,
        IntegerType,
        InfinityType,
        NanType,
        FloatType,
        BoolType,
        DictionaryType,
        DateTimeType,
        NullStringType,
        StringType,
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
            type_hint=None,
            strip_str=None,
            float_type=None,
            datetime_format_str=DefaultValue.DATETIME_FORMAT,
            strict_type_mapping=None,
            replace_tabs_with_spaces=True, tab_length=2,
            east_asian_ambiguous_width=1):
        super(DataProperty, self).__init__(datetime_format_str)

        data = self.__preprocess_data(data, strip_str)
        self.__set_data(data, type_hint, float_type, strict_type_mapping)
        self.__replace_tabs(replace_tabs_with_spaces, tab_length)
        self.__align = align_getter.get_align_from_typecode(self.typecode)

        try:
            integer_digits, decimal_places = get_number_of_digit(data)
        except OverflowError:
            integer_digits = DefaultValue.NAN_VALUE
            decimal_places = DefaultValue.NAN_VALUE
        self.__integer_digits = integer_digits
        self.__decimal_places = decimal_places
        self.__additional_format_len = self.__get_additional_format_len()
        self.__calc_length(east_asian_ambiguous_width)

    def __repr__(self):
        element_list = []

        if self.typecode == Typecode.DATETIME:
            element_list.append(
                "data={:s}".format(six.text_type(self.data)))
        else:
            try:
                element_list.append("data=" + self.to_str())
            except UnicodeEncodeError:
                element_list.append("data={}".format(
                    MultiByteStrDecoder(self.data).unicode_str))
        element_list.extend([
            "typename={:s}".format(self.typename),
            "align={}".format(self.align),
            "str_len={:d}".format(self.str_len),
            "ascii_char_width={:d}".format(self.ascii_char_width),
            "integer_digits={}".format(self.integer_digits),
            "decimal_places={}".format(self.decimal_places),
            "additional_format_len={}".format(self.additional_format_len),
        ])

        return ", ".join(element_list)

    def get_padding_len(self, ascii_char_width):
        return ascii_char_width - (self.ascii_char_width - self.str_len)

    def to_str(self):
        return self.format_str.format(self.data)

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
            raise ValueError(
                "integer digits and decimal places must be greater or equals to zero")

        float_len = self.integer_digits + self.decimal_places
        if self.decimal_places > 0:
            # for dot
            float_len += 1

        return float_len

    def __calc_length(self, east_asian_ambiguous_width):
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
            try:
                self.__str_len = len(self.to_str())
            except ValueError:
                # reach to this line if the year <1900.
                # the datetime strftime() methods require year >= 1900.
                self.__str_len = len(six.text_type(self.data))

            self.__ascii_char_width = self.__str_len
            return

        try:
            unicode_str = MultiByteStrDecoder(self.data).unicode_str
        except ValueError:
            unicode_str = self.to_str()

        self.__str_len = len(unicode_str)
        self.__ascii_char_width = get_ascii_char_width(
            unicode_str, east_asian_ambiguous_width)

    def __preprocess_data(self, data, strip_str):
        if strip_str is None:
            return data

        try:
            return data.strip(strip_str)
        except AttributeError:
            return data
        except UnicodeDecodeError:
            return MultiByteStrDecoder(data).unicode_str.strip(strip_str)

    def __set_data(self, data, type_hint, float_type, strict_type_mapping):
        if float_type is None:
            float_type = DefaultValue.FLOAT_TYPE

        if strict_type_mapping is None:
            strict_type_mapping = DefaultValue.STRICT_TYPE_MAPPING

        if type_hint:
            type_obj = type_hint(
                data, is_strict=False, params={"float_type": float_type})
            self.__typecode = type_obj.typecode
            try:
                self.__data = type_obj.convert()
                return
            except TypeConversionError:
                pass

        for type_class in self.__type_class_list:
            is_strict = strict_type_mapping.get(
                type_class(None).typecode, False)

            if self.__try_convert_type(
                    data, type_class, is_strict, float_type):
                return

        raise TypeConversionError("failed to convert: " + self.typename)

    def __try_convert_type(self, data, type_class, is_strict, float_type):
        type_obj = type_class(data, is_strict, {"float_type": float_type})

        if not type_obj.is_type():
            return False

        self.__typecode = type_obj.typecode
        self.__data = type_obj.convert()

        return True

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
        "__ascii_char_width",
        "__minmax_integer_digits",
        "__minmax_decimal_places",
        "__minmax_additional_format_len",
        "__dataproperty_list",
        "__east_asian_ambiguous_width",
    )

    __TYPE_CLASS_TABLE = {
        Typecode.NONE: NoneType,
        Typecode.NULL_STRING: NullStringType,
        Typecode.STRING: StringType,
        Typecode.INTEGER: IntegerType,
        Typecode.INFINITY: InfinityType,
        Typecode.NAN: NanType,
        Typecode.FLOAT: FloatType,
        Typecode.BOOL: BoolType,
        Typecode.DATETIME: DateTimeType,
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

        return int(min(
            math.ceil(avg + Decimal("1.0")),
            self.minmax_decimal_places.max_value))

    @property
    def typecode(self):
        return self.__get_typecode_from_bitmap()

    @property
    def padding_len(self):
        """
        mark as delete.
        """

        return self.ascii_char_width

    @property
    def ascii_char_width(self):
        if self.typecode != Typecode.FLOAT:
            return self.__ascii_char_width

        max_len = self.__ascii_char_width
        col_format_str = self.format_str

        for dp in self.__dataproperty_list:
            if dp.typecode in [Typecode.INFINITY, Typecode.NAN]:
                continue

            try:
                formatted_value = col_format_str.format(dp.data)
            except (TypeError, ValueError):
                continue

            max_len = max(max_len, get_ascii_char_width(
                formatted_value, self.__east_asian_ambiguous_width))

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
    def type_class(self):
        return self.__TYPE_CLASS_TABLE.get(self.typecode)

    def __init__(
            self, min_padding_len=0,
            datetime_format_str=DefaultValue.DATETIME_FORMAT,
            east_asian_ambiguous_width=1):
        super(ColumnDataProperty, self).__init__(datetime_format_str)

        self.__typecode_bitmap = Typecode.NONE
        self.__str_len = min_padding_len
        self.__ascii_char_width = min_padding_len
        self.__east_asian_ambiguous_width = east_asian_ambiguous_width

        self.__minmax_integer_digits = MinMaxContainer()
        self.__minmax_decimal_places = ListContainer()
        self.__minmax_additional_format_len = MinMaxContainer()
        self.__dataproperty_list = []

    def __repr__(self):
        return ", ".join([
            "typename=" + self.typename,
            "align=" + six.text_type(self.align),
            "ascii_char_width=" + six.text_type(self.ascii_char_width),
            "integer_digits=({:s})".format(
                six.text_type(self.minmax_integer_digits)),
            "decimal_places=({:s})".format(
                six.text_type(self.minmax_decimal_places)),
            "additional_format_len=({:s})".format(
                six.text_type(self.minmax_additional_format_len)),
        ])

    def update_header(self, dataprop):
        self.__str_len = max(self.__str_len, dataprop.str_len)
        self.__ascii_char_width = max(
            self.__ascii_char_width, dataprop.ascii_char_width)

    def update_body(self, dataprop):
        self.__typecode_bitmap |= dataprop.typecode
        self.__str_len = max(self.__str_len, dataprop.str_len)
        self.__ascii_char_width = max(
            self.__ascii_char_width, dataprop.ascii_char_width)

        if dataprop.typecode in (Typecode.FLOAT, Typecode.INTEGER):
            self.__minmax_integer_digits.update(dataprop.integer_digits)
            self.__minmax_decimal_places.update(dataprop.decimal_places)

        self.__minmax_additional_format_len.update(
            dataprop.additional_format_len)

        self.__dataproperty_list.append(dataprop)

    def __is_not_single_typecode(self, typecode):
        return all([
            self.__typecode_bitmap & typecode,
            self.__typecode_bitmap & ~typecode,
        ])

    def __is_float_typecode(self):
        FLOAT_TYPECODE_BMP = Typecode.FLOAT | Typecode.INFINITY | Typecode.NAN
        NUMBER_TYPECODE_BMP = FLOAT_TYPECODE_BMP | Typecode.INTEGER

        if self.__is_not_single_typecode(
                NUMBER_TYPECODE_BMP | Typecode.NULL_STRING):
            return False

        if bin(self.__typecode_bitmap & (
                FLOAT_TYPECODE_BMP | Typecode.NULL_STRING)).count("1") >= 2:
            return True

        if bin(self.__typecode_bitmap & NUMBER_TYPECODE_BMP).count("1") >= 2:
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
            Typecode.NULL_STRING,
        ]

        for typecode in typecode_list:
            if self.__typecode_bitmap & typecode:
                return typecode

        if self.__typecode_bitmap == Typecode.NONE:
            return Typecode.NONE

        return Typecode.STRING
