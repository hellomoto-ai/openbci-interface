"""Define interface to Cyton board"""
import re
import time
import struct
import logging
import warnings

import serial

_LG = logging.getLogger(__name__)

START_BYTE = 0xA0
STOP_BYTE = 0xC0

ADS1299VREF = 4.5
ADS1299GAIN = 24.0
EEG_SCALE = 1000000. * ADS1299VREF / (pow(2, 23)-1) / ADS1299GAIN
AUX_SCALE = 0.002 / pow(2, 4)


def _unpack_aux_data(stop_byte, raw):
    if stop_byte != 0xC0:
        warnings.warn(
            'Data format other than 0xC0 '
            '(Standard with accel) is not implemented.')
    return [v * AUX_SCALE for v in struct.unpack('>hhh', raw)]


def _parse_sample_rate(message):
    pattern = r'(\d+)\s*Hz'
    return int(re.search(pattern, message).group(1))


class Cyton:
    """Interface to Cyton board

    Parameters
    ----------
    port : str
        Serial port, such as ``/dev/cu.usbserial-DM00CXN8``

    baudrate : int
        Baudrate.

    timeout : int
        Read timeout.

    References
    ----------
    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK
    http://docs.openbci.com/Hardware/03-Cyton_Data_Format



    .. automethod:: __enter__

    .. automethod:: __exit__
    """

    num_eeg = 8
    num_aux = 3

    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

        self._streaming = False
        self._wifi_attached = False

    @property
    def streaming(self):
        """Returns the current streaming status."""
        return self._streaming

    def open(self):
        """Open serial port."""
        _LG.info('Connecting to %s (Baud: %s) ...', self.port, self.baudrate)
        self._serial = serial.Serial(
            port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        _LG.info('Connection established.')

    def close(self):
        """Close serial port."""
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


        .. note::
           This method blocks until ``$$$`` string is received.
        """
        msg = self._serial.read_until(b'$$$').decode('utf-8', errors='replace')
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
        """
        _LG.info('Getting firmware version')
        self.write('V')
        return self.read_message().replace('$$$', '')

    def get_board_mode(self):
        """Get the current board mode.

        Returns
        -------
        str
            Board mode.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-board-mode
        """
        _LG.info('Getting board mode...')
        self.write(b'//')
        return self.read_message()

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
        if self._wifi_attached:
            _LG.warning('WiFi already attached.')
            return
        _LG.info('Attaching WiFi shield...')
        self.write(b'{')
        message = self.read_message()
        if 'failed' in message.lower():
            raise RuntimeError(message)
        self._wifi_attached = True

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
        if not self._wifi_attached:
            _LG.warning('No WiFi to detach.')
            return
        _LG.info('Detaching WiFi shield...')
        self.write(b'}')
        message = self.read_message()
        if 'failed' in message.lower():
            raise RuntimeError(message)
        self._wifi_attached = False

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
        """Perform a soft (power) reset of the WiFi shield."""
        _LG.info('Resetting WiFi shield.')
        self.write(b';')

    def start_streaming(self):
        """Start streaming data.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-stream-data-commands
        """
        _LG.info('Start streaming.')
        self.write(b'b')
        self._streaming = True
        if self._wifi_attached:
            self.read_message()

    def stop_streaming(self):
        """Stop streaming data.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-stream-data-commands
        """
        _LG.info('Stop streaming.')
        self.write(b's')
        self._streaming = False
        if self._wifi_attached:
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

        .. code-block:: python

           with Cyton(port, baudrate, timeout) as board:
               board.start_streaming()
               board.read_sample()

        Streaming is stopped and serial connection is closed automatically.
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
        """Read one sample from channels

        Returns
        -------
        dict

            .. code-block:: javascript

               {
                 'eeg': [<channel1>, ..., <channel8>],
                 'aux': [<channel1>, ..., <channel4>],
                 'packet_id': int,
                 'timestamp': float,
               }


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
        aux_raw = self._read_aux_data()
        stop_byte = self._read_stop_byte()
        aux = _unpack_aux_data(stop_byte, aux_raw)
        return {
            'eeg': eeg, 'aux': aux,
            'packet_id': packet_id, 'timestamp': timestamp,
        }

    def _wait_start_byte(self):
        n_skipped = 0
        while True:
            val = struct.unpack('B', self.read())[0]
            if val != START_BYTE:
                n_skipped += 1
                continue
            if n_skipped:
                _LG.warning('Skipped %d bytes at start.', n_skipped)
            return

    def _read_packet_id(self):
        return struct.unpack('B', self.read())[0]

    def _read_eeg_sample(self):
        raw = self.read(3)
        prefix = b'\xFF' if struct.unpack('3B', raw)[0] > 127 else b'\x00'
        return struct.unpack('>i', prefix + raw)[0] * EEG_SCALE

    def _read_eeg_data(self):
        return [self._read_eeg_sample() for _ in range(self.num_eeg)]

    def _read_aux_data(self):
        return self.read(2 * self.num_aux)

    def _read_stop_byte(self):
        return struct.unpack('B', self.read())[0]
