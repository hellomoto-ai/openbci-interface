"""Define fixtures for testing cyton module"""
import logging
from collections import namedtuple

import pytest
import serial as pyserial
from openbci_interface import cyton

_LG = logging.getLogger(__name__)


class SerialMock:
    """Mock Serial by providing the list of expected I/O strings.

    Internally it uses loop back software-based connection.
    """
    def __init__(self, port='loop://', timeout=0.1, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.is_open = False
        self._serial = None
        self._patterns = None

    ###########################################################################
    # Methods for mocking Serial behaviors
    def open(self):
        """Open serial connection"""
        self._serial = pyserial.serial_for_url(
            url=self.port, timeout=self.timeout, baudrate=self.baudrate)
        self.is_open = True

    def close(self):
        """Pseudo clse serial connection,

        Does not close the serial for post inspection purpose,
        but set is_open to False.
        """
        self.is_open = False

    def read(self, size=1):
        return self._serial.read(size)

    def read_until(self, expected=b'\n', size=None):
        return self._serial.read_until(expected, size)

    def write(self, data):
        """Pseudo write method

        It pass the input data through the srial for compatibility check,
        then write the expected reaction message from pre-registered pattern.
        """
        # Pass data through the serial for compatibility validataion
        self._serial.write(data)
        assert data == self._serial.read(len(data))

        # Retrieve the expected message corresponding to the given data
        try:
            expected, message = next(self._patterns)
        except StopIteration:
            raise AssertionError(
                'All the I/O patterns are consumed. '
                'No expected patterns for %s' % data
            ) from None
        if data != expected:
            raise AssertionError(
                'Host sent data that does not match the next expected input. '
                'Expected: `%s`, Found: `%s`' % (expected, data)
            )
        if message is not None:
            self._serial.write(message)

    ###########################################################################
    # Test Pattern related methods
    @property
    def patterns(self):
        raise AttributeError('`patterns` is write only attribute.')

    @patterns.setter
    def patterns(self, patterns):
        """Set the list of I/O patterns that this instance should go through

        Parameters
        ----------
        patterns : list of tuples
            Each tuple consists of (expected_input, expected_output).
            e.g. (b'V', b'v3.1.1$$$')
        """
        _LG.debug('Registering patterns;')
        for pattern in patterns:
            _LG.debug(pattern)
        self._patterns = iter(patterns)

    def validate_no_message_in_buffer(self):
        """Validate that no message-to-be-read is present in Serial buffer"""
        message = self.read()
        if message:
            message += self.read_until(100)
            raise AssertionError(
                'Un-read message found in buffer; %s' % message
            ) from None

    def validate_all_patterns_consumed(self):
        """Validate that all the registered patterns are consumed"""
        try:
            pattern = next(self._patterns)
        except StopIteration:
            pass
        else:
            raise AssertionError(
                'Not all the I/O patterns are consumed. '
                'Remaining patterns starts from: %s' % pattern
            ) from None


@pytest.fixture(scope='function')
def cyton_mock():
    """Instanciate Cyton with SerialMock and inspect buffer at tear down"""
    serial = SerialMock()
    board = cyton.Cyton(port=serial)
    BoardAndSerial = namedtuple('BoardAndSerial', ['board', 'serial'])
    yield BoardAndSerial(board, serial)
    serial.validate_no_message_in_buffer()
    serial.validate_all_patterns_consumed()


@pytest.fixture(scope='function')
def cyton_patch(mocker):
    """Patched version ot cyton_mock for instantiation coverage.

    Use this class when you want to test Cyton(port, baudrate, timeout)
    construction pattern.
    """
    mocker.patch.object(cyton.serial, 'Serial', SerialMock)
    board = cyton.Cyton(port='loop://')
    serial = board._serial
    BoardAndSerial = namedtuple('BoardAndSerial', ['board', 'serial'])
    yield BoardAndSerial(board, serial)
    serial.validate_no_message_in_buffer()
    serial.validate_all_patterns_consumed()


@pytest.fixture(scope='module')
def init_message():
    return b'''OpenBCI V3 8-16 channel
On Board ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v3.1.1
$$$'''
