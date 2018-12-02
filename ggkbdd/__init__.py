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
    """
    :param str path: the path to the device node
    :param libevdev.EventCode mode_key: the mode key
    :param dict macros: a dictionary of macros with the key code as key and
        the value as list of (key code, value) tuples
    """
    def __init__(self, path, mode_key, macros):
        self.fd = open(path, 'r+b', buffering=0)
        # FIXME: O_NONBLOCK
        self._evdev = libevdev.Device(self.fd)

        # We just enable every KEY_* code that the kernel defines.
        # libevdev resolves all undefines ones as KEY_1A2 hex names but
        # since the kernel is unlikely to route those, skip over them.
        d = libevdev.Device()
        d.name = f'GGKBDD {self._evdev.name}'
        for key in libevdev.EV_KEY.codes:
            if (key.name.startswith('KEY_') and
                not key.name == f'KEY_{key.value:03X}'):
                d.enable(key)
        self._uinput = d.create_uinput_device()

        self._mode_key = mode_key
        self._in_macro_mode = False

        self._macros = macros

    def process(self):
        for e in self._evdev.events():
            if not e.matches(libevdev.EV_KEY):
                continue

            # for the mode toggle key, we only process release events.
            # Otherwise we may grab() the device before the release events
            # and the rest of the stack thinks the key is being held down.
            # For actual macro keys, we only care about key presses.
            if not e.value:
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
        self._led_pattern(onoff)

    def _led_pattern(self, onoff):
        leds = [libevdev.EV_LED.LED_NUML,
                libevdev.EV_LED.LED_CAPSL,
                libevdev.EV_LED.LED_SCROLLL]

        # Save the current state, in the hope that nothing will change until
        # we mode-toggle back. Not perfect but good enough most of the time.
        if onoff:
            self._leds = {l: self._evdev.value[l] for l in leds}

        # flash once
        self._evdev.set_leds([(l, 0) for l in leds])
        time.sleep(0.15)
        self._evdev.set_leds([(l, 1) for l in leds])
        time.sleep(0.15)

        # left/right direction marquee
        if onoff:
            self._evdev.set_leds([(l, 0) for l in leds])
        else:
            leds.reverse()
            self._evdev.set_leds([(l, 1) for l in leds])

        time.sleep(0.1)
        for l in leds:
            self._evdev.set_leds([(l, onoff)])
            time.sleep(0.1)

        # restore the previous state
        if not onoff:
            self._evdev.set_leds([(l, v) for l, v in self._leds.items()])

    def _macro(self, event):
        if event.code not in self._macros:
            logger.debug(f'Unbound key {event.code.name}')
            return

        macro = self._macros[event.code]
        for k, v in macro:
            event = InputEvent(k, value=v)
            syn = InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0)
            self._uinput.send_events([event, syn])
            time.sleep(0.008)
        logger.debug(f'Macros sent: {" ".join([x[0].name for x in macro])}')
