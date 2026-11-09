from __future__ import annotations

import sys


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] in {"palette", "palettes"}:
        from .cli import main as palette_main

        return palette_main(argv[1:])
    from .app import main as app_main

    return app_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
