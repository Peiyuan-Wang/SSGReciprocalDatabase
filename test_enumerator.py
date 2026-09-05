#!/usr/bin/env python3

from __future__ import annotations

import unittest
from fractions import Fraction

import sympy as sp

from enumerate_reciprocal_groups import (
    AffineElement,
    close_affine_group,
    common_origin_test,
    fixed_point_test,
    matrix_tuple,
    torus_system,
)


class ReciprocalEnumeratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mirror = matrix_tuple(sp.diag(1, 1, -1))

    def test_klein_glide_is_intrinsic_and_free(self) -> None:
        glide = AffineElement(self.mirror, (Fraction(0), Fraction(1, 2), Fraction(0)))
        self.assertTrue(common_origin_test([glide])["intrinsic_momentum_nonsymmorphic"])
        self.assertFalse(fixed_point_test(glide)["solvable"])
        self.assertEqual(len(close_affine_group([glide])), 2)

    def test_shift_in_reversed_direction_is_removable(self) -> None:
        shifted_mirror = AffineElement(
            self.mirror, (Fraction(0), Fraction(0), Fraction(1, 2))
        )
        self.assertFalse(
            common_origin_test([shifted_mirror])["intrinsic_momentum_nonsymmorphic"]
        )
        self.assertTrue(fixed_point_test(shifted_mirror)["solvable"])

    def test_global_obstruction_can_require_multiple_generators(self) -> None:
        c1 = sp.Matrix([[2]])
        c2 = sp.Matrix([[2]])
        self.assertTrue(torus_system([c1], [(Fraction(0),)])["solvable"])
        self.assertTrue(torus_system([c2], [(Fraction(1, 2),)])["solvable"])
        self.assertFalse(
            torus_system([c1, c2], [(Fraction(0),), (Fraction(1, 2),)])["solvable"]
        )

    def test_antiunitary_identity_spatial_action_is_individually_removable(self) -> None:
        antiunitary = AffineElement(
            matrix_tuple(-sp.eye(3)),
            (Fraction(1, 2), Fraction(0), Fraction(1, 2)),
        )
        self.assertFalse(
            common_origin_test([antiunitary])["intrinsic_momentum_nonsymmorphic"]
        )


if __name__ == "__main__":
    unittest.main()
