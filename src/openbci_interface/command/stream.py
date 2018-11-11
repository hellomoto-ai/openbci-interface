"""Implements ``stream`` command."""
import sys
import json
import time
import logging
import argparse

from serial import Serial
from openbci_interface import Cyton

_LG = logging.getLogger(__name__)


def _parse_args(args):
    parser = argparse.ArgumentParser(
        description='Stream data from an OpenBCI board.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--port', required=True,
        help='Port to which OpenBCI board is connected.'
    )
    parser.add_argument(
        '--baudrate', '--br', type=int,
        help='Baudrate.',
        default=115200,
    )
    parser.add_argument(
        '--timeout', type=int,
    )
    parser.add_argument(
        '--board-type', choices=['cyton', 'ganglion', 'daisy'],
        default='cyton',
    )
    parser.add_argument(
        '--sample-rate', type=int, default=250,
        choices=[250, 500, 1000, 2000, 4000, 8000, 16000],
    )
    parser.add_argument(
        '--board-mode', default='default',
        choices=['default', 'debug', 'analog', 'digital', 'marker'],
    )
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args(args)


def main(args):
    """Entrypoint for ``stream`` command.

    For the detail of the command, use ``stream --help``.
    """
    args = _parse_args(args)

    with Cyton(_get_serial(args)) as board:
        board.set_board_mode(args.board_mode)
        board.get_board_mode()
        board.set_sample_rate(args.sample_rate)
        board.get_sample_rate()
        board.start_streaming()

        period = 0.85 / board.sample_rate
        unit_wait = period / 10.0
        last_acquired = time.time()
        while True:
            now = time.time()
            if now - last_acquired < period:
                time.sleep(unit_wait)
                continue
            sample = board.read_sample()
            last_acquired = now
            sys.stdout.write(json.dumps(sample))
            sys.stdout.write('\n')
            sys.stdout.flush()


def _get_serial(args):
    return Serial(
        port=args.port, baudrate=args.baudrate, timeout=args.timeout,
    )
