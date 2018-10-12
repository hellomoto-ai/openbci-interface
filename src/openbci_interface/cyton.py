"""Define interface to Cyton board"""
import re
import time
import struct
import logging
import warnings

import serial

from openbci_interface import util

_LG = logging.getLogger(__name__)

START_BYTE = 0xA0
STOP_BYTE = 0xC0

ADS1299VREF = 4.5
ADS1299GAIN = 24.0
EEG_SCALE = 1000000. * ADS1299VREF / ADS1299GAIN / (pow(2, 23) - 1)
AUX_SCALE = 0.002 / pow(2, 4)


def _unpack_24bit_signed_int(raw):
    prefix = b'\xFF' if struct.unpack('3B', raw)[0] & 0x80 > 0 else b'\x00'
    return struct.unpack('>i', prefix + raw)[0]


def _unpack_16bit_signed_int(raw):
    prefix = b'\xFF' if struct.unpack('2B', raw)[0] & 0x80 > 0 else b'\x00'
    return struct.unpack('>i', prefix * 2 + raw)[0]


def _unpack_aux_data(stop_byte, raw_data):
    if stop_byte != 0xC0:
        warnings.warn(
            'Stop Byte is %s. Formats other than 0xC0 '
            '(Standard with accel) is not implemented.' % stop_byte)
    return [AUX_SCALE * _unpack_16bit_signed_int(v) for v in raw_data]


def _parse_sample_rate(message):
    pattern = r'(\d+)\s*Hz'
    return int(re.search(pattern, message).group(1))


class Cyton:
    """Interface to Cyton board

    Parameters
    ----------
    port : str or Serial instance.
        Device location, such as ``/dev/cu.usbserial-DM00CXN8``.
        Alternatively you can pass a Serial instance.
        If the given instance is already open, then
        :func:`Cyton.open<openbci_interface.cyton.Cyton.open>`:
        does not call ``open()`` method of the given instance.
        Similary, :func:`Cyton.close<openbci_interface.cyton.Cyton.close>`:
        does not call ``close()`` method of the given instance.
        Therefore when passing an alredy-opened Serial instance, it is
        caller's responsibility to close the connection.

    baudrate : int
        Baudrate.

    timeout : int
        Read timeout.


    :cvar int num_eeg: The number of EEG channels. (8)

    :cvar int num_aux: The number of AUX channels. (3)


    References
    ----------
    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK
    http://docs.openbci.com/Hardware/03-Cyton_Data_Format

    .. automethod:: __enter__

    .. automethod:: __exit__
    """

    num_eeg = 8  # The number of EEG channels.
    num_aux = 3  # The number of AUX channels.

    def __init__(self, port, baudrate=115200, timeout=1):
        if isinstance(port, str):
            self._serial = serial.Serial()
            # Not passing these attribute
            # to constructor to avoid immediate port open,
            self._serial.baudrate = baudrate
            self._serial.timeout = timeout
            self._serial.port = port
        else:
            self._serial = port

        # Wheather Serial.close() should be called in self.close().
        # True when Serial connection was opened by this instance.
        # False when already-opened Serial instance was passed.
        self._close_serial = False

        # Pubclic (read-only) attributes
        # Since a serial communication must happen to alter the statue of
        # board, and these are implemented in method with explicit names,
        # we can use attributes without under score prefix for read-only
        # property.
        self.streaming = False
        self.wifi_attached = False

    def open(self):
        """Open serial port if it is not open yet."""
        if not self._serial.is_open:
            _LG.info(
                'Connecting to %s (Baud: %s) ...',
                self._serial.port, self._serial.baudrate)
            self._serial.open()
            _LG.info('Connection established.')
            self._close_serial = True

    def close(self):
        """Close serial port if it is opened by this class.

        See :func:`__init__<openbci_interface.cyton.Cyton.__init__>`: .
        """
        if self._serial.is_open and self._close_serial:
            _LG.info('Closing connection ...')
            self._serial.close()
            _LG.info('Connection closed.')

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

    def read_message(self):
        """Read OpenBCI-board specific ($$$-terminated) message.

        Returns
        -------
        str
            Message received from the board.
        """
        msg = self._serial.read_until(b'$$$')
        _LG.debug(msg)
        msg = msg.decode('utf-8', errors='replace')
        util.validate_message(msg)
        for line in msg.split('\n'):
            _LG.info('   %s', line)
        return msg

    def initialize(self):
        """Reset the board state.

        Returns
        -------
        str
            Message received from the board.

        References
        ----------
        http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-startup
        """
        _LG.info('Initializing board...')
        self.write(b'v')
        return self.read_message()

    def get_firmware_version(self):
        """Get firmware version

        Returns
        -------
        str
            Version string

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-get-version
        """
        _LG.info('Getting firmware version')
        self.write(b'V')
        return self.read_message().replace('$$$', '')

    def get_board_mode(self):
        """Get the current board mode.

        Returns
        -------
        str or None
            One of ``default``, ``debug``, ``analog``, ``digital``, ``marker``
            if the mode string is parsed successfully. Otherwise None.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-board-mode
        """
        _LG.info('Getting board mode...')
        self.write(b'//')
        message = self.read_message()
        matched = re.search(r'.*\s(\S+)\$\$\$', message)
        if matched:
            return matched.group(1)
        _LG.warning('Failed to parse board mode from the message; %s', message)
        return None

    def set_board_mode(self, mode):
        """Set board mode.

        Parameters
        ----------
        mode : str
            ``default``, ``debug``, ``analog``, ``digital`` or ``marker``

        Returns
        -------
        str
            Message received from the board.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-board-mode
        """
        _LG.info('Setting board mode: %s', mode)
        mode = mode.lower()
        vals = {
            'default': b'0',
            'debug': b'1',
            'analog': b'2',
            'digital': b'3',
            'marker': b'4',
        }
        if mode not in vals:
            raise ValueError('Board mode must be one of %s' % vals.keys())
        command = b'/' + vals[mode]
        self.write(command)
        return self.read_message()

    def get_sample_rate(self):
        """Get the current sample rate.

        Returns
        -------
        int
            Sample rate.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-sample-rate
        """
        _LG.info('Getting sample rate...')
        self.write(b'~~')
        return _parse_sample_rate(self.read_message())

    def set_sample_rate(self, sample_rate):
        """Set the sample rate.

        .. note::
           The Cyton with USB Dongle cannot and will not stream data over
           250SPS.
           Plug in the WiFi Shield to get speeds over 250SPS streaming.
           You may still write to an SD card though, the firmware will not
           send EEG data over the Bluetooth radios.

        Parameters
        ----------
        sample_rate : int
            One of ``250``, ``500``, ``1000``, ``2000``,
            ``4000``, ``8000`` or ``1600``.

        Returns
        -------
        int
            The resulting sample rate.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-sample-rate
        """
        _LG.info('Setting sample rate: %s', sample_rate)
        vals = {
            250: b'6',
            500: b'5',
            1000: b'4',
            2000: b'3',
            4000: b'2',
            8000: b'1',
            16000: b'0',
        }
        if sample_rate not in vals:
            raise ValueError('Sample rate must be one of %s' % vals.keys())
        command = b'~' + vals[sample_rate]
        self.write(command)
        return _parse_sample_rate(self.read_message())

    def attach_wifi(self):
        """Try to attach WiFi shield.

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            When failed to attach WiFi shield.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        """
        if self.wifi_attached:
            _LG.warning('WiFi already attached.')
            return
        _LG.info('Attaching WiFi shield...')
        self.write(b'{')
        message = self.read_message()
        if 'failure' in message.lower():
            raise RuntimeError(message)
        self.wifi_attached = True

    def detach_wifi(self):
        """Try to detach WiFi shield.

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            When failed to detach Wifi shield.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        """
        if not self.wifi_attached:
            _LG.warning('No WiFi to detach.')
            return
        _LG.info('Detaching WiFi shield...')
        self.write(b'}')
        message = self.read_message()
        if 'failure' in message.lower():
            raise RuntimeError(message)
        self.wifi_attached = False

    def get_wifi_status(self):
        """Get the status of WiFi shield.

        Returns
        -------
        str
            Message received from the board.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        """
        _LG.info('Getting WiFi shield status.')
        self.write(b':')
        return self.read_message()

    def reset_wifi(self):
        """Perform a soft (power) reset of the WiFi shield.

        Returns
        -------
        str
            Message received from the board.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        """
        _LG.info('Resetting WiFi shield.')
        self.write(b';')
        self.read_message()

    def enable_channel(self, channel):
        """Turn on channel for sample acquisition

        Parameters
        ----------
        channel : int
            value must be between 1 - 8, inclusive.
        """
        command = {
            1: b'!',
            2: b'@',
            3: b'#',
            4: b'$',
            5: b'%',
            6: b'^',
            7: b'&',
            8: b'*',
        }
        if channel not in command:
            raise ValueError('`channel` value must be in range of [1, 8]')
        self.write(command[channel])

    def disable_channel(self, channel):
        """Turn off channel for sample acquisition

        Parameters
        ----------
        channel : int
            value must be between 1 - 8, inclusive.
        """
        command = {
            1: b'1',
            2: b'2',
            3: b'3',
            4: b'4',
            5: b'5',
            6: b'6',
            7: b'7',
            8: b'8',
        }
        if channel not in command:
            raise ValueError('`channel` value must be in range of [1, 8]')
        self.write(command[channel])

    def start_streaming(self):
        """Start streaming data.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-stream-data-commands
        """
        _LG.info('Start streaming.')
        self.write(b'b')
        self.streaming = True
        if self.wifi_attached:
            self.read_message()

    def stop_streaming(self):
        """Stop streaming data.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-stream-data-commands
        """
        _LG.info('Stop streaming.')
        self.write(b's')
        self.streaming = False
        if self.wifi_attached:
            self.read_message()

    def enable_timestamp(self):
        """Enable timestamp

        Returns
        -------
        str or None
            If board is not streaming, then confirmation message is returned.
            Otherwise, None is returned.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands-time-stamping

        .. note::
           Timestamp parsing is not supported yet.

        .. todo::
           Implement timestamp parsing.

        """
        _LG.info('Enabling timestamp.')
        self.write(b'<')
        if not self.streaming:
            return self.read_message()
        return None

    def disable_timestamp(self):
        """Disable timestamp

        Returns
        -------
        str or None
            If board is not streaming, then confirmation message is returned.
            Otherwise, None is returned.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands-time-stamping
        """
        _LG.info('Disabling timestamp.')
        self.write(b'>')
        if not self.streaming:
            return self.read_message()
        return None

    def set_channels_default(self):
        """Set all channels to default configuration.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-default-channel-settings
        """
        _LG.info('Setting all channels to default.')
        self.write(b'd')
        self.read_message()

    def get_default_settings(self):
        """Get channel default configuration string.

        Returns
        -------
        str
            6 ASCII characters indicating ``POWER_DOWN``, ``GAIN_SET``,
            ``INPUT_TYPE_SET``, ``BIAS_SET``, ``SRB2_SET`` and ``SRB1_SET``,
            See the refernce for the detail.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-default-channel-settings
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-channel-setting-commands
        """
        _LG.info('Getting default channel settings.')
        self.write(b'D')
        return self.read_message().replace('$$$', '')

    def __enter__(self):
        """Context manager for open/close serial connection automatically.

        By utilizing context manager with ``with`` statement, board is
        initialized automatically after serial connection is established.
        Streaming is stopped and serial connection is closed automatically
        at exit.

        .. code-block:: python

           with Cyton(port, baudrate, timeout) as board:
               # no need to call board.initialize()
               board.start_streaming()
               board.read_sample()
               # no need to call board.stop_streaming()

        However when passing an already-opened Serial instance to
        :func:`Cyton<openbci_interface.cyton.Cyton>`, context manager
        does not close the serial.

        .. code-block:: python

           # Passing an instance with open connection
           ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
           with Cyton(ser) as board:
               pass
           assert ser.is_open  # Connection is still open.

        .. code-block:: python

           # Passing an instance with connection not opened yet.
           ser = serial.Serial(baudrate=baudrate, timeout=timeout)
           ser.port = port
           with Cyton(ser) as board:
               pass
           assert ser.is_open  # Connection is closed.
        """
        self.open()
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager for open/close serial connection automatically.

        See :func:`__enter__<openbci_interface.cyton.Cyton.__enter__>`
        """
        if self.streaming:
            self.stop_streaming()
        self.close()
        return exc_type in [None, KeyboardInterrupt]

    def read_sample(self):
        """Read one sample from channels.

        Returns
        -------
        dict

            .. code-block:: javascript

               {
                 'eeg': [<channel1>, ..., <channel8>],
                 'aux': [<channel1>, ..., <channel3>],
                 'packet_id': int,
                 'timestamp': float,
               }


        .. note::
            This method will discard the message received from board
            before receiving start byte.

        .. note::
           The output format is subject to change.

        .. note::
           For AUX data, only ``0xC0`` stop byte is supported now.

        References
        ----------
        http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-binary-format
        """
        self._wait_start_byte()
        timestamp = time.time()
        packet_id = self._read_packet_id()
        eeg = self._read_eeg_data()
        aux_raw_data = self._read_aux_data()
        stop_byte = self._read_stop_byte()
        aux = _unpack_aux_data(stop_byte, aux_raw_data)
        return {
            'eeg': eeg, 'aux': aux,
            'packet_id': packet_id, 'timestamp': timestamp,
        }

    # In sample acquisition methods, do not use `self.read` which logs
    # raw values, and might flood the log
    def _wait_start_byte(self):
        n_skipped = 0
        while True:
            val = self._serial.read()
            if val and struct.unpack('B', val)[0] == START_BYTE:
                break
            n_skipped += 1
        if n_skipped:
            _LG.warning('Skipped %d bytes at start.', n_skipped)

    def _read_packet_id(self):
        return struct.unpack('B', self._serial.read())[0]

    def _read_eeg_sample(self):
        return _unpack_24bit_signed_int(self._serial.read(3)) * EEG_SCALE

    def _read_eeg_data(self):
        return [self._read_eeg_sample() for _ in range(self.num_eeg)]

    def _read_aux_data(self):
        return [self._serial.read(2) for _ in range(self.num_aux)]

    def _read_stop_byte(self):
        return struct.unpack('B', self._serial.read())[0]
