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
tatus.
2018-10-03 22:48:09,001:  INFO:     Wifi not present, send { to attach the shield$$$
2018-10-03 22:48:09,001:  INFO: Start streaming.
{"eeg": [-7028.1931195489315, -6989.770470830259, -7109.017027499322, -7175.781688187324, -143843.8020758393, -168036.70442541892, -175808.00364112898, -170754.56479246198], "aux": [0.012, -0.018000000000000002, 0.506], "packet_id": 0, "timestamp": 1538632089.594613}
{"eeg": [-7163.4882287369055, -7223.055627710299, -7035.68095394146, -6980.919180025957, -143855.31322423377, -168041.04066384325, -175811.26699581946, -170757.559926219], "aux": [0.0, 0.0, 0.0], "packet_id": 1, "timestamp": 1538632089.599571}
{"eeg": [-7155.061621077254, -7174.954673642478, -7070.2814543582745, -7093.147288936054, -143871.47353547497, -168041.57710571017, -175812.4963417645, -170758.76692041958], "aux": [0.0, 0.0, 0.0], "packet_id": 2, "timestamp": 1538632089.6047091}
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
