#!/usr/bin/env python3
"""Run the test suite without triggering Qt teardown crashes.

Qt can segfault while destroying its platform plugin after every test has
already finished. Exiting before that teardown keeps CI reliable; a crash
during the tests themselves still fails the run normally.
"""

from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main() -> None:
    suite = unittest.defaultTestLoader.discover("tests")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
