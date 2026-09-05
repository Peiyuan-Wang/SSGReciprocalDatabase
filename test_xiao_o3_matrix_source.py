#!/usr/bin/env python3

from __future__ import annotations

import unittest
from pathlib import Path

import sympy as sp

from xiao_o3_matrix_source import XiaoO3MatrixSource


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "official_sources" / "iso_ir" / "XiaoO3RepresentationSource.json"


class XiaoO3MatrixSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = XiaoO3MatrixSource(SOURCE)

    def test_complete_xiao_index(self) -> None:
        labels = self.source.labels()
        self.assertEqual(len(labels), 67475)
        self.assertEqual(sum(label.startswith("L") for label in labels), 1421)
        self.assertEqual(sum(label.startswith("P") for label in labels), 9542)
        self.assertEqual(sum(label.startswith("N") for label in labels), 56512)

    def test_suppressed_identity_blocks(self) -> None:
        matrix = self.source.matrix("N2.1.1", 0)
        self.assertEqual(matrix, sp.eye(3))
        self.assertEqual(
            self.source.record("N2.1.1")["Alternatives"][0]["Constituents"],
            ["GM1+", "GM1+", "GM1+"],
        )

    def test_parameterized_sg143_matrix(self) -> None:
        label = "P143.5.1"
        gamma = sp.symbols("gamma", real=True)
        for operator in range(self.source.operator_count(label)):
            matrix = self.source.matrix(
                label, operator, component_parameters=[(0, 0, gamma)]
            )
            self.assertEqual(sp.simplify(matrix.T * matrix), sp.eye(2))
        translation = self.source.primitive_translation_matrix(
            label, 2, component_parameters=[(0, 0, gamma)]
        )
        self.assertEqual(sp.simplify(translation.T * translation), sp.eye(2))
        self.assertNotEqual(translation, sp.eye(2))
        self.assertEqual(sp.simplify(sp.trace(translation)), 2 * sp.cos(2 * sp.pi * gamma))
        self.assertEqual(sp.simplify(translation.det()), 1)

    def test_sg143_bilbao_complex_pair_realification(self) -> None:
        label = "P143.5.2"
        matrices = [
            self.source.matrix(label, operator)
            for operator in range(self.source.operator_count(label))
        ]
        self.assertEqual([sp.simplify(matrix.det()) for matrix in matrices], [1, 1, 1])
        self.assertEqual([sp.simplify(sp.trace(matrix)) for matrix in matrices], [2, -1, -1])

    def test_direct_sum_operator_lists_align(self) -> None:
        label = "N143.11.1"
        count = self.source.operator_count(label)
        self.assertGreater(count, 0)
        for operator in range(count):
            self.assertEqual(self.source.matrix(label, operator).shape, (3, 3))

    def test_uniform_o3_embedding(self) -> None:
        self.assertEqual(
            self.source.embed_o3("L2.1.1", self.source.matrix("L2.1.1", 0)).shape,
            (3, 3),
        )
        coplanar = self.source.matrix("P143.5.2", 1)
        embedded = self.source.embed_o3("P143.5.2", coplanar)
        self.assertEqual(embedded.shape, (3, 3))
        self.assertEqual(sp.simplify(embedded.det()), 1)


if __name__ == "__main__":
    unittest.main()
