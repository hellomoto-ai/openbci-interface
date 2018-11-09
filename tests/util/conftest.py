"""Defines fixtures common to util module testing"""


CYTON_8BIT_FIRMWARE_STRING = b'''OpenBCI V3 8bit Board
Setting ADS1299 Channel Values
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
$$$'''


CYTON_V1_FIRMWARE_STRING = b'''OpenBCI V3 16 channel
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
$$$'''

CYTON_V2_FIRMWARE_STRING = b'''OpenBCI V3 8-16 channel
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v2.0.0
$$$'''

CYTON_V3_FIRMWARE_STRING = b'''OpenBCI V3 8-16 channel
On Board ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v3.1.1
$$$'''

CYTON_V3_WITH_DAISY_FIRMWARE_STRING = b'''OpenBCI V3 8-16 channel
On Board ADS1299 Device ID: 0x3E
On Daisy ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v3.1.1
$$$'''

GANGLION_V2_FIRMWARE_STRING = b'''OpenBCI Ganglion v2.0.0
LIS2DH ID: 0x33
MCP3912 CONFIG_1: 0xXX
$$$'''


class SerialMock:
    """Mock Serial Device"""
    firmware_strings = {
        'foo': b'',
        'bar': b'',
        'cyton_8bit': CYTON_8BIT_FIRMWARE_STRING,
        'cyton_v1': CYTON_V1_FIRMWARE_STRING,
        'cyton_v2': CYTON_V2_FIRMWARE_STRING,
        'cyton_v3': CYTON_V3_FIRMWARE_STRING,
        'daisy_v3': CYTON_V3_WITH_DAISY_FIRMWARE_STRING,
        'ganglion_v2': GANGLION_V2_FIRMWARE_STRING,
    }

    def __init__(self, port, baudrate=None, timeout=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.buffer = None

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        pass

    def write(self, val):
        if val == b'v':
            self.buffer = SerialMock.firmware_strings[self.port]
        else:
            raise ValueError(
                '%s does not support `write` method with value `%s`'
                % (self.__class__.__name__, val)
            )

    def read_until(self, _):
        return self.buffer
