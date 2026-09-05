#!/usr/bin/env python3

from __future__ import annotations

import unittest
from pathlib import Path

from parse_bilbao_representations_html import parse_html


SAMPLE = Path("/Users/wpy/Downloads/representations_sg143.html")


class BilbaoRepresentationsHtmlTests(unittest.TestCase):
    def test_sg143_parametric_line_is_parsed(self) -> None:
        if not SAMPLE.exists():
            self.skipTest("user-supplied Bilbao sample is unavailable")
        result = parse_html(SAMPLE.read_text(encoding="utf-8", errors="replace"))
        self.assertEqual(result["space_group_number"], 143)
        self.assertIn("k1=(0,0,w)", result["k_vector"])
        little = result["matrix_tables"][0]
        self.assertEqual(little["representation_labels"], ["DT1", "DT2", "DT3"])
        self.assertEqual(little["generators"][1]["seitz_symbol"], "{3+001|0,0,0}")
        self.assertEqual(little["generators"][1]["representation_matrices"]["DT1"], "1")
        self.assertEqual(little["generators"][1]["representation_matrices"]["DT2"], "ei2π/3")
        self.assertEqual(little["generators"][1]["representation_matrices"]["DT3"], "e-i2π/3")


if __name__ == "__main__":
    unittest.main()
