"""Constants"""

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
