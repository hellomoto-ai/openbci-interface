"""Implements ``list_devices`` command."""
import sys
import logging
import argparse

from openbci_interface import util

_LG = logging.getLogger(__name__)


def _parse_args(args):
    parser = argparse.ArgumentParser(
        description='List available OpenBCI devices.'
    )
    parser.add_argument(
        '--filter', default='OpenBCI',
        help='Regular expression applied to '
        'firmware information string to filter the result.'
    )
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args(args)


def main(args):
    """Entrypoint for ``list_devices`` command.

    For the detail of the command, use ``list_devices --help``.
    """
    args = _parse_args(args)
    for port in util.list_devices(filter_regex=args.filter):
        sys.stdout.write(port)
        sys.stdout.write('\n')
