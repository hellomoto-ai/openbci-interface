"""Define interface with Cyton"""
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


class Cyton(object):
    """Interface to Cyton board"""

    num_eeg = 8
    num_aux = 3

    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

        self.streaming = False
        self.filtering = False

    def connect(self):
        _LG.info('Connecting: %s:%s', self.port, self.baudrate)
        self._serial = serial.Serial(
            port=self.port, baudrate=self.baudrate, timeout=self.timeout)

        _LG.info('Initializing board...')
        self._serial.write(b'v')
        time.sleep(2)
        for line in self.read_message().split('\n'):
            _LG .info('    %s', line)

        _LG.info('Initialization complete.')

    def close(self):
        _LG.info('Closing connection ...')
        self._serial.close()
        _LG.info('Connection closed.')

    def get_board_mode(self):
        _LG.info('Getting board mode...')
        self._serial.write(b'//')
        message = self.read_message()
        _LG.info('    %s', message)

    def set_board_mode(self, mode):
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
        self._serial.write(command)
        message = self.read_message()
        _LG.info('    %s', message)

    def get_sample_rate(self):
        _LG.info('Getting sample rate...')
        self._serial.write(b'~~')
        message = self.read_message()
        _LG.info('    %s', message)
        return _parse_sample_rate(message)

    def set_sample_rate(self, sample_rate):
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
        self._serial.write(command)
        message = self.read_message()
        _LG.info('    %s', message)
        return _parse_sample_rate(message)

    def attach_wifi(self):
        _LG.info('Attaching WiFi shield.')
        self._serial.write(b'{')
        message = self.read_message()
        _LG.info('    %s', message)
        if 'failed' in message.lower():
            raise RuntimeError(message)

    def remove_wifi(self):
        _LG.info('Removing WiFi shield.')
        self._serial.write(b'}')
        message = self.read_message()
        _LG.info('    %s', message)
        if 'failed' in message.lower():
            raise RuntimeError(message)

    def get_wifi_status(self):
        _LG.info('Getting WiFi shield status.')
        self._serial.write(b':')
        message = self.read_message()
        _LG.info('    %s', message)
        return 'not present' not in message

    def reset_wifi(self):
        _LG.info('Resetting WiFi shield.')
        self._serial.write(b';')

    def start_streaming(self):
        _LG.info('Start streaming.')
        self._serial.write(b'b')
        self.streaming = True

    def stop_streaming(self):
        _LG.info('Stop streaming.')
        self._serial.write(b's')
        self.streaming = False

    def enable_filters(self):
        _LG.info('Enable filtering.')
        self._serial.write(b'f')
        self.filtering = True

    def disable_filters(self):
        _LG.info('Disable filtering.')
        self._serial.write(b'g')
        self.filtering = False

    def enable_timestamp(self):
        _LG.info('Enabling timestamp.')
        self._serial.write(b'<')

    def disable_timestamp(self):
        _LG.info('Disabling timestamp.')
        self._serial.write(b'>')

    def set_channels_default(self):
        _LG.info('Setting all channels to default.')
        self._serial.write(b'd')
        _LG.info('    %s', self.read_message())

    def get_default_settings(self):
        _LG.info('Getting default channel settings.')
        self._serial.write(b'D')
        message = self.read_message()
        _LG.info('    %s', message)
        return message

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_streaming()
        self.close()
        return exc_type in [None, KeyboardInterrupt]

    def read_message(self):
        return self._serial.read_until(b'$$$').decode('utf-8', errors='replace')

    def read_sample(self):
        """Read one sample from board"""
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
            val = struct.unpack('B', self._serial.read())[0]
            if val != START_BYTE:
                n_skipped += 1
                continue
            if n_skipped:
                _LG.warning('Skipped %d bytes at start.', n_skipped)
            return

    def _read_packet_id(self):
        return struct.unpack('B', self._serial.read())[0]

    def _read_eeg_sample(self):
        raw = self._serial.read(3)
        prefix = b'\xFF' if struct.unpack('3B', raw)[0] > 127 else b'\x00'
        return struct.unpack('>i', prefix + raw)[0] * EEG_SCALE

    def _read_eeg_data(self):
        return [self._read_eeg_sample() for _ in range(self.num_eeg)]

    def _read_aux_data(self):
        return self._serial.read(2 * self.num_aux)

    def _read_stop_byte(self):
        return struct.unpack('B', self._serial.read())[0]
