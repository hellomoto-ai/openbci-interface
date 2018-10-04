# OpenBCI Interface

Simple Python inferface with OpenBCI Cyton Board.

Currently only Cyton with USB dongle is supported.

# Getting Started

## Install the codebase

```bash
pip isntall git+https://github.com/hellomoto-ai/openbci-interface.git
```

## Check the installation.

After successful installation, you have `openbci_interface` command.

```bash
$ openbci_interface --version
OpenBCI Interface 0.1.0
```

## Stream data using command line.

### Connect your board.

Connect your board, following [the official instruction](http://docs.openbci.com/Tutorials/00-Tutorials).


### List available devices.

`list_devices` subcommand will list up the available OpenBCI boards.

```bash
$ openbci_interface list_devices
/dev/cu.usbserial-DM00CXN8
```


### Stream data from a device.

`stream` subcommand will stream data from a board.

```bash
$ openbci_interface stream --port /dev/cu.usbserial-DM00CXN8
2018-10-04 00:57:08,587:  INFO: Connecting: /dev/cu.usbserial-DM00CXN8:115200
2018-10-04 00:57:08,592:  INFO: Initializing board...
2018-10-04 00:57:10,597:  INFO:     OpenBCI V3 8-16 channel
2018-10-04 00:57:10,598:  INFO:     On Board ADS1299 Device ID: 0x3E
2018-10-04 00:57:10,598:  INFO:     LIS3DH Device ID: 0x33
2018-10-04 00:57:10,598:  INFO:     Firmware: v3.1.1
2018-10-04 00:57:10,598:  INFO:     $$$
2018-10-04 00:57:10,598:  INFO: Initialization complete.
2018-10-04 00:57:10,598:  INFO: Setting all channels to default.
2018-10-04 00:57:10,684:  INFO:     updating channel settings to default$$$
2018-10-04 00:57:10,684:  INFO: Getting default channel settings.
2018-10-04 00:57:10,780:  INFO:     060110$$$
2018-10-04 00:57:10,780:  INFO: Setting board mode: default
2018-10-04 00:57:10,876:  INFO:     Success: default$$$
2018-10-04 00:57:10,876:  INFO: Setting sample rate: 250
2018-10-04 00:57:11,421:  INFO:     Success: Sample rate is 250Hz$$$
2018-10-04 00:57:11,421:  INFO: Getting WiFi shield status.
2018-10-04 00:57:11,533:  INFO:     Wifi not present, send { to attach the shield$$$
2018-10-04 00:57:11,533:  INFO: Start streaming.
{"eeg": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "aux": [0.032, -0.028, 1.004], "packet_id": 0, "timestamp": 1538639831.6448839}
{"eeg": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "aux": [0.0, 0.0, 0.0], "packet_id": 1, "timestamp": 1538639832.124458}
...
```

Use `--help` command to see the other available options.


## Use as Python module

Currently Cyton board is available as `openbci_interface.Cyton`.

```python
import time
from openbci_interface import Cyton

sample_rate = 250
baudrate = 115200
port = '/dev/cu.usbserial-DM00CXN8'

with Cython(port, baudrate) as board:
    board.set_board_mode('default')
    board.set_sample_rate(sample_rate)
    board.start_streaming()
    while True:
        sample = board.read_sample()
        time.sleep(0.95 / sample_rate)
```
