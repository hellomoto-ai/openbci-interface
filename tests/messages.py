"""Constants"""

CYTON_8BIT_INFO = b'''OpenBCI V3 8bit Board
Setting ADS1299 Channel Values
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
$$$'''


CYTON_V1_INFO = b'''OpenBCI V3 16 channel
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
$$$'''

CYTON_V2_INFO = b'''OpenBCI V3 8-16 channel
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v2.0.0
$$$'''

CYTON_V3_INFO = b'''OpenBCI V3 8-16 channel
On Board ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v3.1.1
$$$'''

CYTON_V3_WITH_DAISY_INFO = b'''OpenBCI V3 8-16 channel
On Board ADS1299 Device ID: 0x3E
On Daisy ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v3.1.1
$$$'''

GANGLION_V2_INFO = b'''OpenBCI Ganglion v2.0.0
LIS2DH ID: 0x33
MCP3912 CONFIG_1: 0xXX
$$$'''

RESET_CHANNEL = b'updating channel settings to default$$$'

STREAM_STARTED = b'Stream started$$$'
STREAM_STOPPED = b'Stream stopped$$$'

DAISY_ALREADY_ATTACHED = b'16$$$'
DAISY_ATTACHED = b'daisy attached16$$$'
NO_DAISY_TO_ATTACH = b'no daisy to attach!8$$$'
DAISY_REMOVED = b'daisy removed$$$'

TIMESTAMP_ON = b'Time stamp ON$$$'
TIMESTAMP_OFF = b'Time stamp OFF$$$'

SAMPLE_RATE_250 = b'Success: Sample rate is 250Hz$$$'
SAMPLE_RATE_500 = b'Success: Sample rate is 500Hz$$$'
SAMPLE_RATE_1000 = b'Success: Sample rate is 1000Hz$$$'
SAMPLE_RATE_2000 = b'Success: Sample rate is 2000Hz$$$'
SAMPLE_RATE_4000 = b'Success: Sample rate is 4000Hz$$$'
SAMPLE_RATE_8000 = b'Success: Sample rate is 8000Hz$$$'
SAMPLE_RATE_16000 = b'Success: Sample rate is 16000Hz$$$'

BOARD_MODE_DEFAULT = b'Success: default$$$'
BOARD_MODE_DEBUG = b'Success: debug$$$'
BOARD_MODE_ANALOG = b'Success: analog$$$'
BOARD_MODE_DIGITAL = b'Success: digital$$$'
BOARD_MODE_MARKER = b'Success: marker$$$'

WIFI_ATTACH_SUCCESS = b'Success: Wifi attached$$$'
WIFI_ATTACH_FAILURE = b'Failure: Wifi not attached$$$'
WIFI_REMOVE_SUCCESS = b'Success: Wifi removed$$$'
WIFI_REMOVE_FAILURE = b'Failure: Wifi not removed$$$'
WIFI_PRESENT = b'Wifi present$$$'
WIFI_NOT_PRESENT = b'Wifi not present, send { to attach the shield$$$'
WIFI_RESET = b'Wifi soft reset$$$'

SET_CHANNEL_1 = b'Success: Channel set for 1$$$'
SET_CHANNEL_2 = b'Success: Channel set for 2$$$'
SET_CHANNEL_3 = b'Success: Channel set for 3$$$'
SET_CHANNEL_4 = b'Success: Channel set for 4$$$'
SET_CHANNEL_5 = b'Success: Channel set for 5$$$'
SET_CHANNEL_6 = b'Success: Channel set for 6$$$'
SET_CHANNEL_7 = b'Success: Channel set for 7$$$'
SET_CHANNEL_8 = b'Success: Channel set for 8$$$'
SET_CHANNEL_9 = b'Success: Channel set for 9$$$'
SET_CHANNEL_10 = b'Success: Channel set for 10$$$'
SET_CHANNEL_11 = b'Success: Channel set for 11$$$'
SET_CHANNEL_12 = b'Success: Channel set for 12$$$'
SET_CHANNEL_13 = b'Success: Channel set for 13$$$'
SET_CHANNEL_14 = b'Success: Channel set for 14$$$'
SET_CHANNEL_15 = b'Success: Channel set for 15$$$'
SET_CHANNEL_16 = b'Success: Channel set for 16$$$'
