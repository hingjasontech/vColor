#!/usr/bin/env python3
"""Run the test suite without triggering Qt teardown crashes.

Qt can crash while destroying its platform plugin after every test has
already finished. Exit before that teardown keeps CI reliable; a crash
during the tests themselves still fails the run normally.
"""

from __future__ import annotations

import faulthandler
import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
faulthandler.enable()


def _exit(code: int) -> None:
    sys.stdout.flush()
    sys.stderr.flush()
    if sys.platform == "win32":
        # os._exit still runs DLL detach handlers on Windows, where Qt can
        # crash. TerminateProcess skips them and keeps the test exit code.
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateProcess.restype = wintypes.BOOL
        kernel32.TerminateProcess(kernel32.GetCurrentProcess(), code)
    os._exit(code)


def main() -> None:
    suite = unittest.defaultTestLoader.discover("tests")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    _exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
