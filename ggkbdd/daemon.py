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
import libevdev
import configparser
import os
import sys
import xdg.BaseDirectory
from ggkbdd import Keyboard

import logging
logging.basicConfig(format='%(levelname)s: %(name)s: %(message)s',
                    level=logging.INFO)
base_logger = logging.getLogger('ggkbdd')
logger = logging.getLogger('ggkbdd.daemon')


class Daemon(object):
    def __init__(self, paths, config_path):
        mode_key, macros = self._read_config(config_path)
        self.keyboards = []
        for p in paths:
            self.keyboards.append(Keyboard(p, mode_key, macros))

    def run(self):
        while True:
            # FIXME: use poll here
            for k in self.keyboards:
                k.process()

    def _read_config(self, config_path):
        if not os.path.exists(config_path):
            raise Exception(f'Missing config file {config_path}')

        config = configparser.ConfigParser()
        # disable the lowercase conversion
        config.optionxform = lambda option: option
        config.read(config_path)
        if ('General' not in config.sections() or
            'Macros' not in config.sections()):
            raise Exception('Invalid Config file, sections missing')
        entry = config['General'].get('ModeKey')
        if entry is None:
            raise Exception(f'Missing entry ModeKey')
        mode_key = libevdev.evbit(f'KEY_{entry}')
        if mode_key is None:
            raise Exception(f'Unable to map ModeKey={entry}')

        macros = {}
        for key, value in config['Macros'].items():
            keybit = libevdev.evbit(f'KEY_{key}')
            if keybit is None:
                raise Exception(f'Unable to map key {key}')

            macro = []
            for m in value.split(' '):
                keyname = m
                press = True
                release = True
                if m[0] == '+':  # press only
                    keyname = m[1:]
                    release = False
                elif m[0] == '-':  # release only
                    keyname = m[1:]
                    press = False
                bit = libevdev.evbit(f'KEY_{keyname}')
                if bit is None:
                    raise Exception(f'Unable to map key {keyname}')
                if press:
                    macro.append((bit, 1))
                if release:
                    macro.append((bit, 0))

            macros[keybit] = macro

        return mode_key, macros


def main():
    parser = argparse.ArgumentParser(description='A generic gaming keyboard daemon')
    parser.add_argument('device', metavar='/dev/input/event0',
                        type=str, help='Path to the keyboard device')
    parser.add_argument('--config', type=str, help='Path to config file',
                        default=os.path.join(xdg.BaseDirectory.xdg_config_home, 'ggkbddrc'))
    parser.add_argument('--verbose', action='store_true',
                        default=False, help='Show debugging information')
    args = parser.parse_args()
    if args.verbose:
        base_logger.setLevel(logging.DEBUG)

    try:
        daemon = Daemon([args.device], args.config)
    except PermissionError:
        logger.error(f'Failed to open {args.device}: Permission denied')
        sys.exit(1)

    try:
        daemon.run()
    except KeyboardInterrupt:
        pass
