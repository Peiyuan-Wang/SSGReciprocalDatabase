#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bilbao_repres_source import (
    build_url,
    classify_payload,
    request_id,
    store_attempt,
)


class BilbaoRepresSourceTests(unittest.TestCase):
    def test_url_preserves_fraction_and_bcs_label(self) -> None:
        url = build_url("text", 75, "Z", ("0", "0", "1/2"), "p")
        self.assertIn("g=75", url)
        self.assertIn("z=1%2F2", url)
        self.assertIn("l=Z", url)

    def test_request_id_is_stable_and_file_safe(self) -> None:
        self.assertEqual(request_id(75, "Z", ("0", "0", "1/2"), "p"), "sg075_Z_0_0_1_2_p")

    def test_turnstile_is_never_accepted_as_data(self) -> None:
        status, _ = classify_payload(b'<div class="cf-turnstile">challenge</div>', 0, "")
        self.assertEqual(status, "BLOCKED_TURNSTILE")

    def test_complete_text_response_is_cached_with_hash(self) -> None:
        payload = b"""# Bilbao Crystallographic Server\n# Result for group 75[ P 4]\n# k-vector = Z(0, 0, 1/2)\nNumber of generators : 4\nNumber of elements : 8\n#end of REPRES\n"""
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            record = store_attempt(
                cache,
                space_group=75,
                label="Z",
                coordinates=("0", "0", "1/2"),
                basis="p",
                endpoint="text",
                url="https://example.invalid",
                payload=payload,
                curl_returncode=0,
                stderr="",
                force=False,
            )
            self.assertEqual(record["status"], "FETCHED_TEXT")
            self.assertEqual(record["request_id"], "sg075_Z_0_0_1_2_p_text")
            self.assertTrue(record["eligible_for_parent_irrep_import"])
            self.assertEqual(record["parsed_summary"]["number_of_generators"], 4)
            index = json.loads((cache / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["usable_record_count"], 1)
            self.assertEqual(len(record["raw_sha256"]), 64)

    def test_server_error_is_stored_but_not_eligible(self) -> None:
        payload = b"Status: 500\nContent-type: text/html\n<h1>Software error:</h1>"
        with tempfile.TemporaryDirectory() as directory:
            record = store_attempt(
                Path(directory),
                space_group=75,
                label="Z",
                coordinates=("0", "0", "1/2"),
                basis="p",
                endpoint="xml",
                url="https://example.invalid",
                payload=payload,
                curl_returncode=0,
                stderr="",
                force=False,
            )
            self.assertEqual(record["status"], "BLOCKED_SERVER_ERROR")
            self.assertFalse(record["eligible_for_parent_irrep_import"])


if __name__ == "__main__":
    unittest.main()
