from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone

from vcolor.updater import (
    ReleaseInfo,
    check_due,
    is_newer,
    parse_version,
    release_from_payload,
)


class VersionTests(unittest.TestCase):
    def test_parse_version_strips_prefix_and_suffix(self) -> None:
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("1.2.3-beta.1"), (1, 2, 3))
        self.assertEqual(parse_version("release-2.0"), (2, 0))
        self.assertEqual(parse_version("none"), ())

    def test_newer_compares_numerically(self) -> None:
        self.assertTrue(is_newer("1.0.1", "1.0.0"))
        self.assertTrue(is_newer("1.10.0", "1.9.9"))
        self.assertTrue(is_newer("2.0", "1.9.9"))

    def test_newer_needs_a_strictly_larger_version(self) -> None:
        self.assertFalse(is_newer("1.0.0", "1.0.0"))
        self.assertFalse(is_newer("1.0", "1.0.0"))
        self.assertFalse(is_newer("0.9.9", "1.0.0"))
        self.assertFalse(is_newer("garbage", "1.0.0"))


class CheckDueTests(unittest.TestCase):
    def test_missing_timestamp_is_due(self) -> None:
        self.assertTrue(check_due(None))

    def test_recent_timestamp_is_not_due(self) -> None:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
        self.assertFalse(check_due((now - timedelta(hours=1)).isoformat(), now))

    def test_old_timestamp_is_due(self) -> None:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
        self.assertTrue(check_due((now - timedelta(days=2)).isoformat(), now))

    def test_invalid_timestamp_is_due(self) -> None:
        self.assertTrue(check_due("not a date"))


class ReleasePayloadTests(unittest.TestCase):
    def payload(self, **overrides: object) -> bytes:
        raw = {
            "tag_name": "v1.2.0",
            "name": "vColor 1.2.0",
            "html_url": "https://github.com/hingjasontech/vColor/releases/tag/v1.2.0",
            "draft": False,
            "prerelease": False,
        }
        raw.update(overrides)
        return json.dumps(raw).encode("utf-8")

    def test_parses_stable_release(self) -> None:
        release = release_from_payload(self.payload())
        self.assertIsNotNone(release)
        assert release is not None
        self.assertEqual(release.version, "1.2.0")
        self.assertEqual(release.tag, "v1.2.0")

    def test_ignores_drafts_and_prereleases(self) -> None:
        self.assertIsNone(release_from_payload(self.payload(draft=True)))
        self.assertIsNone(release_from_payload(self.payload(prerelease=True)))

    def test_ignores_malformed_payloads(self) -> None:
        self.assertIsNone(release_from_payload(b"not json"))
        self.assertIsNone(release_from_payload(b"[]"))
        self.assertIsNone(release_from_payload(json.dumps({"tag_name": ""}).encode()))

    def test_release_info_is_hashable(self) -> None:
        release = ReleaseInfo(version="1.2.0", tag="v1.2.0", url="u", name="n")
        self.assertEqual({release}, {release})


if __name__ == "__main__":
    unittest.main()
