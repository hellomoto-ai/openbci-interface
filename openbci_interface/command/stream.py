"""Entrypoint for `stream` command."""
import sys
import json
import time
import logging
import argparse

from openbci_interface.cyton import Cyton

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
    """Entrypoint for `test_connection` command"""
    args = _parse_args(args)

    with _get_board(args) as board:
        board.set_channels_default()
        board.get_default_settings()
        board.set_board_mode(args.board_mode)
        board.set_sample_rate(args.sample_rate)
        board.get_wifi_status()
        board.start_streaming()
        while True:
            sys.stdout.write(json.dumps(board.read_sample()))
            sys.stdout.write('\n')
            sys.stdout.flush()
            time.sleep(0.95 / args.sample_rate)


def _get_board(args):
    if args.board_type == 'cyton':
        return Cyton(args.port, args.baudrate, args.timeout)
    raise NotImplementedError('Currently only Cyton is supported.')
