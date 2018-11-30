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

import time
import libevdev
from libevdev import InputEvent
import logging
logger = logging.getLogger('ggkbdd')


class Keyboard(object):
    def __init__(self, path):
        self.fd = open(path, 'rb')
        # FIXME: O_NONBLOCK
        self._evdev = libevdev.Device(self.fd)

        d = libevdev.Device(self.fd)
        d.name = f'{d.name} macro mode'
        self._uinput = d.create_uinput_device()

        # FIXME: configurable
        self._mode_key = libevdev.EV_KEY.KEY_CAPSLOCK
        self._in_macro_mode = False

        # FIXME: configurable, obviously
        self._macros = {
                libevdev.EV_KEY.KEY_S: [libevdev.EV_KEY.KEY_A, libevdev.EV_KEY.KEY_B]
                }

    def process(self):
        for e in self._evdev.events():
            if not e.matches(libevdev.EV_KEY):
                continue

            # we don't care about key releases
            if not e.value:
                continue

            if e.matches(libevdev.EV_KEY.KEY_ESC):
                self._toggle_mode(False)

            if e.matches(self._mode_key):
                self._toggle_mode(not self._in_macro_mode)
                continue

            if not self._in_macro_mode:
                continue

            # we're in macro mode and a different key has been pressed
            self._macro(e)

    def _toggle_mode(self, onoff):
        if self._in_macro_mode == onoff:
            return

        self._in_macro_mode = onoff
        logger.debug(f'Mode enabled: {onoff}')
        if self._in_macro_mode:
            self._evdev.grab()
        else:
            self._evdev.ungrab()

    def _macro(self, event):
        if event.code not in self._macros:
            logger.debug(f'Unbound key {event.code.name}')
            return

        macro = self._macros[event.code]
        for k in macro:
            press = InputEvent(k, value=1)
            release = InputEvent(k, value=0)
            syn = InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0)
            self._uinput.send_events([press, syn])
            time.sleep(0.008)
            self._uinput.send_events([release, syn])
        logger.debug(f'Macros sent: {", ".join([x.name for x in macro])}')
