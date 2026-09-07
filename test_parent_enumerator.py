#!/usr/bin/env python3

from __future__ import annotations

import json
import unittest
from pathlib import Path

import sympy as sp
from sympy.matrices.normalforms import hermite_normal_form

from enumerate_parent_sg import (
    _coboundary_equivalent,
    _gl_coordinate_form,
    _minimal_shift_representative,
    analyze_ssg,
    analyze_ssg_iso_ir,
    center_lattice_from_commutator,
    identify_reciprocal_space_group,
    normalize_label,
    parse_constituents,
)


HERE = Path(__file__).resolve().parent


class ParentSpaceGroupEnumeratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = json.loads(
            (HERE / "parent_irrep_cache" / "sg6_irreps.json").read_text(encoding="utf-8")
        )

    def test_unknown_constituent_is_not_replaced_by_trivial_irrep(self) -> None:
        available = {
            normalize_label(record["label"]): record for record in self.parent["irreps"]
        }
        with self.assertRaises(KeyError):
            parse_constituents("GM2 ⊕ G1GA1", available, 3)

    def test_antiunitary_translation_coset_creates_global_obstruction(self) -> None:
        result = analyze_ssg(
            {
                "id": "N6.9.7",
                "parent_sg": 6,
                "classification_row_raw": "GM2 ⊕ A1 ⊕ Y1 1 1 × - -",
                "xiao_table_nonsymmorphic": True,
            },
            self.parent,
        )
        self.assertEqual(result["status"], "COMPLETE")
        self.assertTrue(result["origin_test"]["intrinsic_momentum_nonsymmorphic"])
        self.assertTrue(result["agreement_with_xiao_nonsymmorphic_flag"])
        translation = result["generator_derivation"][0]
        self.assertEqual(translation["physical_role"], "antiunitary translation coset")
        self.assertEqual(translation["kappa"], [0, 1, 0])

    def test_unitary_common_axis_witness_is_reproduced(self) -> None:
        result = analyze_ssg(
            {
                "id": "N6.9.19",
                "parent_sg": 6,
                "classification_row_raw": "GM2 ⊕ C1 ⊕ C2 1 1 × - -",
                "xiao_table_nonsymmorphic": True,
            },
            self.parent,
        )
        generator = result["generator_derivation"][0]
        self.assertEqual(generator["det_rho"], 1)
        self.assertEqual(generator["eta_g"], -1)
        self.assertEqual(generator["kappa"], [0, 1, 0])
        self.assertEqual(generator["Q"], [0, "1/2", 0])
        self.assertTrue(result["origin_test"]["intrinsic_momentum_nonsymmorphic"])

    def test_coplanar_zeta_shift_is_computed_not_assumed_zero(self) -> None:
        removable = analyze_ssg(
            {
                "id": "P6.2.4",
                "parent_sg": 6,
                "classification_row_raw": "C1 1 1 2/m Ag",
                "xiao_table_nonsymmorphic": False,
            },
            self.parent,
        )
        intrinsic = analyze_ssg(
            {
                "id": "P6.3.5",
                "parent_sg": 6,
                "classification_row_raw": "GM2 ⊕ Z1 1 1 × - -",
                "xiao_table_nonsymmorphic": True,
            },
            self.parent,
        )
        self.assertEqual(removable["generator_derivation"][-1]["kappa"], [0, 1, 1])
        self.assertFalse(removable["origin_test"]["intrinsic_momentum_nonsymmorphic"])
        self.assertEqual(intrinsic["generator_derivation"][-1]["kappa"], [0, 0, 1])
        self.assertTrue(intrinsic["origin_test"]["intrinsic_momentum_nonsymmorphic"])

    @staticmethod
    def classification_record(lattice: list[list[int]], generators: list[dict]) -> dict:
        return {
            "id": "test",
            "status": "COMPLETE",
            "physical_bloch_basis_parent_coordinates": lattice,
            "input_generators": generators,
        }

    def test_u1_coboundary_identifies_removable_half_shift(self) -> None:
        mirror = [[1, 0, 0], [0, 1, 0], [0, 0, -1]]
        shifted = self.classification_record(
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [{"name": "m", "s": 1, "A": mirror, "Q": [0, 0, "1/2"]}],
        )
        zero = self.classification_record(
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [{"name": "m", "s": 1, "A": mirror, "Q": [0, 0, 0]}],
        )
        self.assertTrue(_coboundary_equivalent(shifted, zero))
        self.assertEqual(_minimal_shift_representative(shifted)["nonzero_Q_count"], 0)

    def test_different_embedded_bloch_lattices_remain_distinct(self) -> None:
        action = [{"name": "g", "s": 1, "A": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "Q": [0, 0, 0]}]
        doubled_x = self.classification_record(
            [[2, 0, 0], [0, 1, 0], [0, 0, 1]], action
        )
        doubled_y = self.classification_record(
            [[1, 0, 0], [0, 2, 0], [0, 0, 1]], action
        )
        self.assertFalse(_coboundary_equivalent(doubled_x, doubled_y))

    def test_gl_basis_change_of_same_embedded_lattice_has_same_hnf(self) -> None:
        lattice = sp.diag(2, 1, 1)
        basis_change = sp.Matrix([[0, 1, 0], [1, 1, 0], [0, 0, -1]])
        self.assertEqual(abs(int(basis_change.det())), 1)
        self.assertEqual(
            hermite_normal_form(lattice * basis_change),
            hermite_normal_form(lattice),
        )

    def test_gl_coordinate_form_transforms_A_and_Q_consistently(self) -> None:
        lattice = [[2, 0, 0], [0, 1, 0], [0, 0, 1]]
        representative = {
            "generator_actions": [
                {
                    "name": "g",
                    "s": 1,
                    "A": [[1, 0, 0], [0, -1, 0], [0, 0, 1]],
                    "Q": ["1/2", 0, 0],
                }
            ]
        }
        basis_change = sp.Matrix([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
        transformed = _gl_coordinate_form(lattice, representative, basis_change)
        action = transformed["generator_actions"][0]
        self.assertEqual(
            transformed["bloch_lattice_basis_parent_coordinates"],
            [[0, 2, 0], [0, 0, 1], [1, 0, 0]],
        )
        self.assertEqual(action["A"], [[1, 0, 0], [0, 1, 0], [0, 0, -1]])
        self.assertEqual(action["Q"], [0, "1/2", 0])

    def test_global_obstruction_minimizes_to_one_nonzero_shift(self) -> None:
        anti_identity = [[-1, 0, 0], [0, -1, 0], [0, 0, -1]]
        record = self.classification_record(
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [
                {"name": "a", "s": -1, "A": anti_identity, "Q": [0, 0, 0]},
                {"name": "b", "s": -1, "A": anti_identity, "Q": [0, "1/2", 0]},
            ],
        )
        minimal = _minimal_shift_representative(record)
        self.assertEqual(minimal["nonzero_Q_count"], 1)

    def test_reciprocal_space_group_identification_distinguishes_pm_and_pc(self) -> None:
        mirror = [[1, 0, 0], [0, 1, 0], [0, 0, -1]]

        def reciprocal_class(shift: list[object]) -> dict:
            return {
                "class_id": "test",
                "hnf_representative": {
                    "generator_actions": [
                        {"name": "m", "s": 1, "A": mirror, "Q": shift}
                    ]
                },
            }

        symmorphic = identify_reciprocal_space_group(reciprocal_class([0, 0, 0]))
        glide = identify_reciprocal_space_group(reciprocal_class(["1/2", 0, 0]))
        self.assertEqual(symmorphic["international_number"], 6)
        self.assertEqual(glide["international_number"], 7)

    def test_center_lattice_is_radical_of_noncommuting_translation_form(self) -> None:
        commutator = sp.Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
        center = center_lattice_from_commutator(commutator)
        self.assertEqual(center, sp.diag(2, 2, 1))
        product = commutator.T * center
        self.assertTrue(all(int(value) % 2 == 0 for value in product))

    def test_n143_noncommuting_raw_shift_is_one_coboundary(self) -> None:
        result = analyze_ssg_iso_ir("N143.16.1")
        self.assertEqual(result["translation_projectivity"], "noncommuting")
        self.assertEqual(
            result["physical_bloch_basis_parent_coordinates"],
            [[2, 0, 0], [0, 2, 0], [0, 0, 1]],
        )
        generator = result["generator_derivation"][0]
        self.assertEqual(generator["kappa"], [1, 0, 0])
        self.assertEqual(generator["Q"], ["1/2", 0, 0])
        self.assertTrue(result["origin_test"]["solvable"])
        self.assertFalse(result["origin_test"]["intrinsic_momentum_nonsymmorphic"])

        action = sp.Matrix(result["input_generators"][0]["A"])
        theta = sp.Matrix([sp.Rational(1, 2), sp.Rational(1, 2), 0])
        raw_q = sp.Matrix([sp.Rational(1, 2), 0, 0])
        residual = raw_q - (sp.eye(3) - action) * theta
        self.assertTrue(all(sp.frac(value) == 0 for value in residual))

    def test_iso_ir_backed_n6_witness_has_complete_reciprocal_group(self) -> None:
        result = analyze_ssg_iso_ir("N6.9.19")
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["source_convention"],
                         "ISO-IR Miller-Love/CDML and primitive direct-lattice coordinates")
        self.assertEqual(result["physical_bloch_basis_parent_coordinates"],
                         [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        self.assertEqual(result["input_generators"][0]["s"], 1)
        self.assertEqual(result["input_generators"][0]["Q"], ["1/2", 0, 0])
        self.assertFalse(result["origin_test"]["solvable"])


if __name__ == "__main__":
    unittest.main()
