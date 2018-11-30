#!/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import argparse
import sys
from ggkbdd import Keyboard

import logging
logging.basicConfig(format='%(levelname)s: %(name)s: %(message)s',
                    level=logging.INFO)
base_logger = logging.getLogger('ggkbdd')
logger = logging.getLogger('ggkbdd.daemon')


class Daemon(object):
    def __init__(self, paths):
        self.keyboards = []
        for p in paths:
            self.keyboards.append(Keyboard(p))

    def run(self):
        while True:
            # FIXME: use poll here
            for k in self.keyboards:
                k.process()


def main():
    parser = argparse.ArgumentParser(description='A generic gaming keyboard daemon')
    parser.add_argument('device', metavar='/dev/input/event0',
                        type=str, help='Path to the keyboard device')
    parser.add_argument('--verbose', action='store_true',
                        default=False, help='Show debugging information')
    args = parser.parse_args()
    if args.verbose:
        base_logger.setLevel(logging.DEBUG)

    try:
        daemon = Daemon([args.device])
    except PermissionError:
        logger.error(f'Failed to open {args.device}: Permission denied')
        sys.exit(1)

    try:
        daemon.run()
    except KeyboardInterrupt:
        pass
