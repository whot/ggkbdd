ggkbdd
======

This project is a generic gaming keyboard daemon.

**This is just a proof of concept right now**

The basic functionality is:
- one key is designated as the **mode toggle key**
- keys can be configured to play **macros**
- when the user presses the **mode toggle key**, the keyboard switches to
  the **macro mode**.
  - when pressing a macro key, the configured macro sequence is replayed
  - any non-configured key events are discarded now
- when the user presses `Esc` or the **mode toggle key** again, the keyboard
  switches back to **normal mode**

How does it work
================

ggkbdd runs as root and listens to keyboard events. It also creates a virtual
keyboard device through uinput.

In **macro mode**, ggkbdd grabs the keyboard device so no other client can
receive events. This makes it appear as if the device is in a special mode.

When key presses for configured keys are received, the configured sequence
is simply replayed on the uinput device.

This all happens just above the kernel level, there's no desktop integration
and this happens silently without the rest of the system knowing.

How to run
==========

Use `evemu-record` or `libinput record` to figure out the device node of
your keyboard device. Then use this as argument here:

```
> sudo ./ggkbdd.py --verbose /dev/input/event3
```

The **mode toggle key** is hardcoded to CapsLock.

Right now, a single key is hardcoded as macro key: `s` translates to `ab`.

About
=====

The name ggkbdd was chosen to make it as weird as possible to type. You're
welcome.
