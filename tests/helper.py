import pathlib
import struct

import numpy as _numpy
from pprint import PrettyPrinter
from igor2.binarywave import load as loadibw

data_dir = pathlib.Path(__file__).parent / "data"

# Igor writes this in the 32-byte bname field when the real name follows
# the version 5 sections. See issue 32.
LONG_WAVE_NAME_PLACEHOLDER = b':wave name too long:'


def version7_from_version5(source, name, order, replace_bname=True):
    """Return version 5 bytes relabeled as a version 7 long-name wave.

    ``name`` is appended after the version 5 sections and recorded in
    ``optionsSize1``. The numeric payload is left unchanged.
    """
    data = bytearray(source)
    if order == '<':
        if data[:2] != b'\x05\x00':
            raise ValueError(data[:2])
        data[:2] = b'\x07\x00'
        data[56:60] = struct.pack('<i', len(name))
    elif order == '>':
        if data[:2] != b'\x00\x05':
            raise ValueError(data[:2])
        data[:2] = b'\x00\x07'
        data[56:60] = struct.pack('>i', len(name))
    else:
        raise ValueError(order)
    if replace_bname:
        field = LONG_WAVE_NAME_PLACEHOLDER
        data[92:124] = field + b'\x00' * (32 - len(field))
    if name:
        data.extend(name)
    return bytes(data)


class NumpyPrettyPrinter(PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, _numpy.ndarray):
            # Generate the entire array string using numpy's own mechanism but
            # ensuring dtype is displayed
            array_repr = _numpy.array2string(object, separator=', ')
            # Append dtype only once for the whole array
            formatted_array = f"array({array_repr}, dtype='{object.dtype}')"
            return (formatted_array, True, False)
        # Default handling for other types
        return super().format(object, context, maxlevels, level)


def custom_pformat(object, indent=1, width=80, depth=None, *, compact=False):
    printer = NumpyPrettyPrinter(
        indent=indent, width=width, depth=depth, compact=compact)
    return printer.pformat(object)


def assert_equal_dump_no_whitespace_no_byte(data_a, data_b):
    def repl(x):
        for old, new in [
            [" ", ""],  # ignore whitespaces
            ["b'", "'"],  # ignore bytes vs str
            ["\n", ""],  # ignore newlines
            # treat all floats as equal
            ["float32", "float"],
            ["float64", "float"],
            ["'>f4'", "float"],
            ["'>f8'", "float"],
            ["'float'", "float"],
        ]:
            x = x.replace(old, new)
        return x

    a = repl(data_a)
    b = repl(data_b)
    print("DBUG data_a: ", a)
    print("DBUG data_b: ", b)
    assert a == b


def dumpibw(filename):
    path = data_dir / filename
    data = loadibw(path)
    return format_data(data)


def format_data(data):
    lines = custom_pformat(data).splitlines()
    return '\n'.join([line.rstrip() for line in lines])


def walk_callback(dirpath, key, value):
    return 'walk callback on ({}, {}, {})'.format(
        dirpath, key, '{...}' if isinstance(value, dict) else value)
