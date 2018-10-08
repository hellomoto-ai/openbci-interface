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
    def __init__(self):
        self._patterns = None

        self.port = None
        self.baudrate = None
        self.timeout = None

        self._serial = None

    ###########################################################################
    # Methods for mocking Serial behaviors
    def open(self):
        self._serial = pyserial.serial_for_url(
            url='loop://', timeout=self.timeout, baudrate=self.baudrate)

    def close(self):
        # Not closing the serial for post-inspection.
        pass

    def read(self, size=1):
        return self._serial.read(size)

    def read_until(self, expected=b'\n', size=None):
        return self._serial.read_until(expected, size)

    def write(self, data):
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
        _LG.debug('Registering patterns;')
        for pattern in patterns:
            _LG.debug(pattern)
        self._patterns = iter(patterns)

    def validate_no_message_in_buffer(self):
        message = self.read()
        if message:
            message += self.read_until(100)
            raise AssertionError(
                'Un-read message found in buffer; %s' % message
            ) from None

    def validate_all_patterns_consumed(self):
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
    board = cyton.Cyton(port='foo', timeout=0.1, serial_obj=serial)
    board.open()
    CytonMock = namedtuple('CytonMock', ['board', 'serial'])
    yield CytonMock(board, serial)
    serial.validate_no_message_in_buffer()
    serial.validate_all_patterns_consumed()
