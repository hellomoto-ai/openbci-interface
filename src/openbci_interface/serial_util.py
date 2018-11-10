"""Implement serial utilities"""
import logging

import serial

_LG = logging.getLogger(__name__)


class SerialWrapper:
    """

    Parameters
    ----------
    port : str or Serial instance.
        Device location, such as ``/dev/cu.usbserial-DM00CXN8``.
        Alternatively you can pass a Serial instance.
        If the given instance is already open, then
        :func:`SerialWrapper.open<openbci_interface.core.SerialWrapper.open>`:
        does not call ``Serial.open()`` method of the given instance.
        Similary,
        :func:`SerialWrapper.close<openbci_interface.core.SerialWrapper.close>`:
        does not call ``Serial.close()`` method of the given instance.
        Therefore when passing an alredy-opened Serial instance, it is
        caller's responsibility to close the connection.

    baudrate : int
        Baudrate.

    timeout : int
        Read timeout.
    """
    def __init__(self, port, baudrate=115200, timeout=1):
        if isinstance(port, str):
            self._serial = serial.Serial(baudrate=baudrate, timeout=timeout)
            # Not passing `port` so as to avoid immediate port open.
            self._serial.port = port
        else:
            self._serial = port

        # Wheather Serial.close() should be called in self.close().
        # True when Serial connection was opened by this instance.
        # False when already-opened Serial instance was passed.
        self._close_serial = False

    @property
    def is_open(self):
        """True if serial is open."""
        return self._serial.is_open

    def open(self):
        """Open serial port if it is not open yet.

        See :func:`__init__<openbci_interface.core.Common.__init__>`: .
        """
        if self.is_open:
            return
        ser = self._serial
        _LG.info('Connecting to %s (Baud: %s) ...', ser.port, ser.baudrate)
        ser.open()
        _LG.info('Connection established.')
        self._close_serial = True

    def close(self):
        """Close serial port if it is opened by this class.

        See :func:`__init__<openbci_interface.core.Common.__init__>`: .
        """
        if self.is_open and self._close_serial:
            _LG.info('Closing connection ...')
            self._serial.close()
            _LG.info('Connection closed.')
            self._close_serial = False

    def write(self, value):
        """Write string to serial port.

        Parameters
        ----------
        value : bytes
            Value to write to serial port.
        """
        _LG.debug(value)
        self._serial.write(value)

    def read(self, size=1):
        """Read bytestring from serial port.

        Parameters
        ----------
        Size : int
            Number of bytes to read.

        Returns
        -------
        bytes
            Bytes read from the port.
        """
        value = self._serial.read(size)
        _LG.debug(value)
        return value

    def read_until(self, terminator, size=None):
        """Read bytestring until expected pattern is found or timeout occurs

        Parameters
        ----------
        terminator : bytes
            The byte string to search for.

        size : int
            Number of bytes to read.

        Returns
        -------
        bytes
            Bytes read from the port.
        """
        value = self._serial.read_until(terminator, size)
        _LG.debug(value)
        return value
