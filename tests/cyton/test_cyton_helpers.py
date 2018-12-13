"""Test support functions in cyton module."""
import os
import struct

import pytest
from openbci_interface import cyton, core

# pylint: disable=protected-access
# pylint: disable=bad-whitespace


def _load_patterns(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, 'r') as fileobj:
        for line in fileobj:
            line = line.strip()
            if not line:
                continue
            vals = [int(val) for val in line.split()]
            raw = struct.pack('b' * len(vals[:-1]), *vals[:-1])
            expected = vals[-1]
            yield raw, expected


def test_interpret_16bit_as_int32():
    """interpret16bitAsInt32 works same way as official java example

    http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-16-bit-signed-data-values
    """
    for raw, expected in _load_patterns('16bit_patterns.txt'):
        assert core._interpret_16bit_as_int32(raw) == expected


def test_interpret_24bit_as_int32():
    """interpret24bitAsInt32 works same way as official java example

    http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-24-bit-signed-data-values
    """
    for raw, expected in _load_patterns('24bit_patterns.txt'):
        assert core._interpret_24bit_as_int32(raw) == expected


@pytest.mark.parametrize('raw_eeg,expected', [
    (b'\xd1+\x02',    -68601.57175082824),
    (b'\xcd\x81\x13', -73968.47146373648),
    (b'\xcf\xcf\x1d', -70592.24046376234),
    (b'\xcf_C',       -71232.26031449561),
    (b'\xce\xf4U',    -71844.11696721519),
    (b'\x03_\xce',    4942.730658379872),
    (b'\x03U\x92',    4884.169087906967),
    (b'\x03\\I',      4922.59173662564),
])
def test_parse_eeg(raw_eeg, expected):
    """EEG values are parsed from bytes
    """
    raw_eeg = core._interpret_24bit_as_int32(raw_eeg)
    output = cyton._parse_eeg(raw_eeg, gain=24)
    assert output == expected


@pytest.mark.parametrize('raw_aux,expected', [
    (
        [b'\x01\xb0', b'\x07\x10', b'\x1c\xc0'],
        [0.054, 0.226, 0.92],
    ),
])
def test_parse_aux(raw_aux, expected):
    """AUX values are parsed from bytes"""
    raw_aux = [core._interpret_16bit_as_int32(d) for d in raw_aux]
    output = cyton._parse_aux(0xC0, raw_aux)
    assert output == expected
