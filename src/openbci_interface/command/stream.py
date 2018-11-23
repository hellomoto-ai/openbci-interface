"""Implements ``stream`` command."""
import sys
import json
import sched
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
        board.set_sample_rate(args.sample_rate)
        board.start_streaming()
        try:
            _run(board)
        except KeyboardInterrupt:
            pass


def _periodic(scheduler, interval, func):
    scheduler.enter(interval, 1, _periodic, (scheduler, interval, func))
    func()


def _run(board):
    def _process():
        sample = board.read_sample()
        sys.stdout.write(json.dumps(sample))
        sys.stdout.write('\n')
        sys.stdout.flush()
    scheduler = sched.scheduler()
    interval = board.cycle
    scheduler.enter(interval, 1, _periodic, (scheduler, interval, _process))
    scheduler.run(blocking=True)


def _get_serial(args):
    return Serial(
        port=args.port, baudrate=args.baudrate, timeout=args.timeout,
    )
