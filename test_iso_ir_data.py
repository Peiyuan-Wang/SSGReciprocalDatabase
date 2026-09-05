#!/usr/bin/env python3

from __future__ import annotations

import unittest
from pathlib import Path

from audit_all_xiao_iso_ir_coverage import expand_o3_constituents, representation_descriptor
from audit_xiao_iso_ir_coverage import parse_alternatives
from iso_ir_data import read_iso_ir


HERE = Path(__file__).resolve().parent
PIR = HERE / "official_sources" / "iso_ir" / "PIR_data.txt"


class ISOIRDataTests(unittest.TestCase):
    def test_xiao_alternative_parser(self) -> None:
        self.assertEqual(parse_alternatives("DT2DU2 DT3DU3"), [("DT2DU2",), ("DT3DU3",)])
        self.assertEqual(
            parse_alternatives("(A1, DT2DU2) (A1, DT3DU3)"),
            [("A1", "DT2DU2"), ("A1", "DT3DU3")],
        )

    def test_appendix_representation_descriptor(self) -> None:
        self.assertEqual(representation_descriptor("GM1 3 3 1 A⊕A⊕A"), ("GM1",))
        self.assertEqual(
            representation_descriptor("D1+ D2+ ⊕ GM1− 1 1 × - -"),
            ("D1+D2+", "GM1-"),
        )

    def test_suppressed_identity_expansion(self) -> None:
        self.assertEqual(expand_o3_constituents("N", 1, ("GM1+",), "GM1+"), (("GM1+",) * 3, 3))
        self.assertEqual(
            expand_o3_constituents("N", 2, ("R1-",), "GM1+"),
            (("GM1+", "GM1+", "R1-"), 3),
        )
        self.assertEqual(
            expand_o3_constituents("P", 6, ("DT1DU1",), "GM1"),
            (("DT1DU1",), 2),
        )

    def test_first_pir_records(self) -> None:
        records = read_iso_ir(PIR, "PIR")
        first = next(records)
        self.assertEqual((first.space_group, first.label, first.dimension), (1, "GM1", 1))
        for _ in range(8):
            record = next(records)
        self.assertEqual((record.space_group, record.label, record.dimension), (1, "GP1GQ1", 2))
        self.assertFalse(record.k_special)


if __name__ == "__main__":
    unittest.main()
