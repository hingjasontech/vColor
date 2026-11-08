"""Check GitHub Releases for a newer vColor version.

The checker is deliberately lightweight: it asks the public GitHub API for the
latest stable release once a day, compares the tag against the running version,
and lets the UI decide how to present the result. It never downloads or replaces
the application itself.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

REPOSITORY = "hingjasontech/vColor"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPOSITORY}/releases/latest"
REQUEST_TIMEOUT_MS = 7000
USER_AGENT = "vColor-updater"
CHECK_INTERVAL = timedelta(hours=24)

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


@dataclass(frozen=True, slots=True)
class ReleaseInfo:
    """A stable GitHub release, normalized for display."""

    version: str
    tag: str
    url: str
    name: str


def parse_version(text: str) -> tuple[int, ...]:
    """Return the leading numeric parts of a version string.

    ``v1.2.3-beta.1`` becomes ``(1, 2, 3)`` and anything without a number
    becomes an empty tuple, which callers treat as "not comparable".
    """
    match = _VERSION_RE.search(text or "")
    if match is None:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(candidate: str, current: str) -> bool:
    """Return whether ``candidate`` is a strictly newer version than ``current``."""
    left = parse_version(candidate)
    right = parse_version(current)
    if not left:
        return False
    width = max(len(left), len(right))
    left = left + (0,) * (width - len(left))
    right = right + (0,) * (width - len(right))
    return left > right


def check_due(last_checked: str | None, now: datetime | None = None) -> bool:
    """Return whether the automatic check interval has elapsed."""
    if not last_checked:
        return True
    try:
        previous = datetime.fromisoformat(last_checked)
    except ValueError:
        return True
    if previous.tzinfo is None:
        previous = previous.replace(tzinfo=timezone.utc)
    moment = now or datetime.now(timezone.utc)
    return moment - previous >= CHECK_INTERVAL


def release_from_payload(raw: bytes) -> ReleaseInfo | None:
    """Parse a GitHub release payload, ignoring drafts and prereleases."""
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("draft") or payload.get("prerelease"):
        return None
    tag = str(payload.get("tag_name") or "").strip()
    if not tag:
        return None
    version = tag[1:] if tag[:1] in {"v", "V"} else tag
    if not parse_version(version):
        return None
    return ReleaseInfo(
        version=version,
        tag=tag,
        url=str(payload.get("html_url") or RELEASES_PAGE),
        name=str(payload.get("name") or tag),
    )


class UpdateChecker(QObject):
    """Asynchronous GitHub release lookup built on Qt's network stack."""

    updateAvailable = Signal(object)
    checkFinished = Signal(bool)

    def __init__(self, current_version: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self._manager = QNetworkAccessManager(self)
        self._manager.finished.connect(self._handle_reply)
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def check(self) -> bool:
        """Start a lookup. Returns ``False`` when one is already running."""
        if self._busy:
            return False
        request = QNetworkRequest(QUrl(LATEST_RELEASE_URL))
        request.setTransferTimeout(REQUEST_TIMEOUT_MS)
        request.setHeader(
            QNetworkRequest.KnownHeaders.UserAgentHeader,
            USER_AGENT,
        )
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        self._busy = True
        self._manager.get(request)
        return True

    def _handle_reply(self, reply: QNetworkReply) -> None:
        self._busy = False
        payload = bytes(reply.readAll())
        failed = reply.error() != QNetworkReply.NetworkError.NoError
        reply.deleteLater()

        release = None if failed else release_from_payload(payload)
        if release is None:
            self.checkFinished.emit(False)
            return
        self.checkFinished.emit(True)
        if is_newer(release.version, self.current_version):
            self.updateAvailable.emit(release)
