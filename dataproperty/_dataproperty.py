# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import re

import six
from mbstrdecoder import MultiByteStrDecoder
from typepy import (
    Bool,
    DateTime,
    Dictionary,
    Infinity,
    Integer,
    IpAddress,
    List,
    Nan,
    NoneType,
    NullString,
    RealNumber,
    StrictLevel,
    String,
    Typecode,
    TypeConversionError,
)

from ._align_getter import align_getter
from ._base import DataPeropertyBase
from ._common import DefaultValue
from ._function import calc_ascii_char_width, get_number_of_digit, strip_ansi_escape
from ._line_break import LineBreakHandling


_RE_LINE_BREAK = re.compile("[\r\n]+")


class DataProperty(DataPeropertyBase):
    __slots__ = (
        "__data",
        "__no_ansi_escape_data",
        "__align",
        "__integer_digits",
        "__additional_format_len",
        "__length",
        "__ascii_char_width",
    )

    __type_class_list = [
        NoneType,
        Integer,
        Infinity,
        Nan,
        IpAddress,
        RealNumber,
        Bool,
        List,
        Dictionary,
        DateTime,
        NullString,
        String,
    ]

    @property
    def align(self):
        if not self.__align:
            if self.is_include_ansi_escape:
                self.__align = self.no_ansi_escape_dp.align
            else:
                self.__align = align_getter.get_align_from_typecode(self.typecode)

        return self.__align

    @property
    def decimal_places(self):
        """
        :return:
            Decimal places if the ``data`` type either ``float`` or
            ``decimal.Decimal``. Returns ``0`` if the ``data`` type is ``int``.
            Otherwise, returns ``float("nan")``.
        :rtype: int
        """

        if not self._decimal_places:
            self.__set_digit()

        return self._decimal_places

    @property
    def data(self):
        """
        :return: Original data value.
        :rtype: Original data type.
        """

        return self.__data

    @property
    def is_include_ansi_escape(self):
        if self.no_ansi_escape_dp is None:
            return False

        return self.length != self.no_ansi_escape_dp.length

    @property
    def no_ansi_escape_dp(self):
        return self.__no_ansi_escape_data

    @property
    def length(self):
        """
        :return: Length of the ``data``.
        :rtype: int
        """

        if not self.__length:
            self.__length = self.__get_length()

        return self.__length

    @property
    def ascii_char_width(self):
        if not self.__ascii_char_width:
            self.__ascii_char_width = self.__calc_ascii_char_width()

        return self.__ascii_char_width

    @property
    def integer_digits(self):
        """
        :return:
            Integer digits if the ``data`` type either
            ``int``/``float``/``decimal.Decimal``.
            Otherwise, returns ``None``.
        :rtype: int
        """

        if not self.__integer_digits:
            self.__set_digit()

        return self.__integer_digits

    @property
    def additional_format_len(self):
        if not self.__additional_format_len:
            self.__additional_format_len = self.__get_additional_format_len()

        return self.__additional_format_len

    def __init__(
        self,
        data,
        type_hint=None,
        strip_str=None,
        float_type=None,
        format_flags=None,
        datetime_format_str=DefaultValue.DATETIME_FORMAT,
        strict_level_map=None,
        replace_tabs_with_spaces=True,
        tab_length=2,
        line_break_handling=None,
        is_escape_html_tag=False,
        east_asian_ambiguous_width=1,
    ):
        super(DataProperty, self).__init__(
            format_flags=format_flags,
            is_formatting_float=True,
            datetime_format_str=datetime_format_str,
            east_asian_ambiguous_width=east_asian_ambiguous_width,
        )

        self.__additional_format_len = None
        self.__align = None
        self.__ascii_char_width = None
        self.__integer_digits = None
        self.__length = None

        data, no_ansi_escape_data = self.__preprocess_string(
            self.__process_line_break(self.__preprocess_data(data, strip_str), line_break_handling),
            replace_tabs_with_spaces,
            tab_length,
            is_escape_html_tag,
        )

        self.__set_data(data, type_hint, float_type, strict_level_map)

        if no_ansi_escape_data is None or len(data) == len(no_ansi_escape_data):
            self.__no_ansi_escape_data = None
        else:
            self.__no_ansi_escape_data = DataProperty(no_ansi_escape_data)

    def __eq__(self, other):
        if self.typecode != other.typecode:
            return False

        if self.typecode == Typecode.NAN:
            return True

        return self.data == other.data

    def __ne__(self, other):
        if self.typecode != other.typecode:
            return True

        if self.typecode == Typecode.NAN:
            return False

        return self.data != other.data

    def __repr__(self):
        element_list = []

        if self.typecode == Typecode.DATETIME:
            element_list.append("data={:s}".format(six.text_type(self.data)))
        else:
            try:
                element_list.append("data=" + self.to_str())
            except UnicodeEncodeError:
                element_list.append("data={}".format(MultiByteStrDecoder(self.data).unicode_str))

        element_list.extend(
            [
                "type={:s}".format(self.typename),
                "align={}".format(self.align.align_string),
                "ascii_width={:d}".format(self.ascii_char_width),
            ]
        )

        if Integer(self.length).is_type():
            element_list.append("length={}".format(self.length))

        if Integer(self.integer_digits).is_type():
            element_list.append("int_digits={}".format(self.integer_digits))

        if Integer(self.decimal_places).is_type():
            element_list.append("decimal_places={}".format(self.decimal_places))

        if Integer(self.additional_format_len).is_type():
            element_list.append("extra_len={}".format(self.additional_format_len))

        return ", ".join(element_list)

    def get_padding_len(self, ascii_char_width):
        if self.typecode == Typecode.LIST:
            return max(
                ascii_char_width
                - (
                    self.ascii_char_width
                    - DataProperty(MultiByteStrDecoder(str(self.data)).unicode_str).length
                ),
                0,
            )

        try:
            return max(ascii_char_width - (self.ascii_char_width - self.length), 0)
        except TypeError:
            return ascii_char_width

    def to_str(self):
        return self.format_str.format(self.data)

    def __get_additional_format_len(self):
        if not RealNumber(self.data, strip_ansi_escape=False).is_type():
            return 0

        format_len = 0

        if float(self.data) < 0:
            # for minus character
            format_len += 1

        return format_len

    def __get_base_float_len(self):
        if any([self.integer_digits < 0, self.decimal_places < 0]):
            raise ValueError("integer digits and decimal places must be greater or equals to zero")

        float_len = self.integer_digits + self.decimal_places
        if self.decimal_places > 0:
            # for dot
            float_len += 1

        return float_len

    def __get_length(self):
        if self.typecode in (Typecode.DICTIONARY, Typecode.LIST, Typecode.STRING):
            return len(self.data)

        return None

    def __calc_ascii_char_width(self):
        if self.typecode == Typecode.INTEGER:
            return self.integer_digits + self.additional_format_len

        if self.typecode == Typecode.REAL_NUMBER:
            return self.__get_base_float_len() + self.additional_format_len

        if self.typecode == Typecode.DATETIME:
            try:
                return len(self.to_str())
            except ValueError:
                # reach to this line if the year <1900.
                # the datetime strftime() methods require year >= 1900.
                return len(six.text_type(self.data))

        if self.is_include_ansi_escape:
            return self.no_ansi_escape_dp.ascii_char_width

        try:
            unicode_str = MultiByteStrDecoder(self.data).unicode_str
        except ValueError:
            unicode_str = self.to_str()

        return calc_ascii_char_width(unicode_str, self._east_asian_ambiguous_width)

    @staticmethod
    def __preprocess_data(data, strip_str):
        if strip_str is None:
            return data

        try:
            return data.strip(strip_str)
        except AttributeError:
            return data
        except UnicodeDecodeError:
            return MultiByteStrDecoder(data).unicode_str.strip(strip_str)

    def __set_data(self, data, type_hint, float_type, strict_level_map):
        if float_type is None:
            float_type = DefaultValue.FLOAT_TYPE

        if strict_level_map is None:
            strict_level_map = DefaultValue.STRICT_LEVEL_MAP

        if type_hint:
            type_obj = type_hint(
                data, strict_level=StrictLevel.MIN, float_type=float_type, strip_ansi_escape=False
            )
            self._typecode = type_obj.typecode
            self.__data = type_obj.try_convert()

            if type_hint(
                self.__data,
                strict_level=StrictLevel.MAX,
                float_type=float_type,
                strip_ansi_escape=False,
            ).is_type():
                return

        for type_class in self.__type_class_list:
            strict_level = strict_level_map.get(type_class(None).typecode, False)

            if self.__try_convert_type(data, type_class, strict_level, float_type):
                return

        raise TypeConversionError(
            "failed to convert: data={}, strict_level={}".format(data, strict_level_map)
        )

    def __set_digit(self):
        integer_digits, decimal_places = get_number_of_digit(self.__data)
        self.__integer_digits = integer_digits
        self._decimal_places = decimal_places

    def __try_convert_type(self, data, type_class, strict_level, float_type):
        type_obj = type_class(data, strict_level, float_type=float_type, strip_ansi_escape=False)

        try:
            self.__data = type_obj.convert()
        except TypeConversionError:
            return False

        self._typecode = type_obj.typecode

        return True

    def __preprocess_string(
        self, raw_data, replace_tabs_with_spaces, tab_length, is_escape_html_tag
    ):
        data = raw_data

        if replace_tabs_with_spaces:
            try:
                data = data.replace("\t", " " * tab_length)
            except (TypeError, AttributeError):
                pass

        if is_escape_html_tag:
            if six.PY2:
                import cgi

                data = cgi.escape(data)
            else:
                import html

                try:
                    data = html.escape(data)
                except AttributeError:
                    return (data, None)

        try:
            return (data, strip_ansi_escape(data))
        except TypeError:
            return (data, None)

    @staticmethod
    def __process_line_break(data, line_break_handling):
        if line_break_handling is None or line_break_handling == LineBreakHandling.NOP:
            return data

        try:
            if line_break_handling == LineBreakHandling.REPLACE:
                return _RE_LINE_BREAK.sub(" ", data)

            if line_break_handling == LineBreakHandling.ESCAPE:
                return data.replace("\n", "\\n").replace("\r", "\\r")
        except (TypeError, AttributeError):
            return data

        raise ValueError("unexpected line_break_handling: {}".format(line_break_handling))
