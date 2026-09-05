#!/usr/bin/env python3
"""Enumerate reciprocal affine groups from generator-level SSG data.

The input basis is the physical Bloch-lattice basis.  A generator acts by

    k -> A_g k + Q_g,   A_g = s_g M_g^{-T},

on R^d/Z^d.  All arithmetic is exact.  The program closes the generated
affine group, tests whether one common momentum-origin shift removes every
Q_g, and diagnoses fixed points of the resulting torus action.

This file deliberately does not infer generator matrices from an SSG label.
Records without generator-level data must remain blocked upstream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Sequence

import sympy as sp
from sympy.polys.domains import ZZ
from sympy.polys.matrices import DomainMatrix
from sympy.polys.matrices.normalforms import smith_normal_decomp


def frac(value: object) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    if isinstance(value, list) and len(value) == 2:
        return Fraction(int(value[0]), int(value[1]))
    raise TypeError(f"cannot parse rational value {value!r}")


def mod_one(value: Fraction) -> Fraction:
    return value % 1


def qtuple(values: Sequence[object]) -> tuple[Fraction, ...]:
    return tuple(mod_one(frac(value)) for value in values)


def matrix_tuple(matrix: sp.Matrix) -> tuple[tuple[int, ...], ...]:
    if any(not value.is_Integer for value in matrix):
        raise ValueError(f"matrix is not integral: {matrix}")
    return tuple(tuple(int(matrix[i, j]) for j in range(matrix.cols)) for i in range(matrix.rows))


def matrix_from_tuple(values: Sequence[Sequence[int]]) -> sp.Matrix:
    matrix = sp.Matrix(values)
    if matrix.rows != matrix.cols:
        raise ValueError("linear action must be square")
    if any(not value.is_Integer for value in matrix):
        raise ValueError("linear action must be integral")
    return matrix


@dataclass(frozen=True, order=True)
class AffineElement:
    linear: tuple[tuple[int, ...], ...]
    shift: tuple[Fraction, ...]

    @property
    def dimension(self) -> int:
        return len(self.shift)

    def compose(self, other: "AffineElement") -> "AffineElement":
        """Return self after other: self(other(k))."""

        if self.dimension != other.dimension:
            raise ValueError("dimension mismatch")
        left = sp.Matrix(self.linear)
        right = sp.Matrix(other.linear)
        shift = left * sp.Matrix(other.shift) + sp.Matrix(self.shift)
        return AffineElement(
            matrix_tuple(left * right),
            tuple(mod_one(Fraction(value)) for value in shift),
        )

    def as_json(self) -> dict:
        return {
            "A": [list(row) for row in self.linear],
            "Q": [rational_json(value) for value in self.shift],
        }


def rational_json(value: Fraction) -> int | str:
    return value.numerator if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def identity(dimension: int) -> AffineElement:
    return AffineElement(matrix_tuple(sp.eye(dimension)), (Fraction(0),) * dimension)


def close_affine_group(
    generators: Sequence[AffineElement], max_order: int = 4096
) -> tuple[AffineElement, ...]:
    if not generators:
        raise ValueError("at least one generator is required")
    dimension = generators[0].dimension
    if any(generator.dimension != dimension for generator in generators):
        raise ValueError("all generators must have the same dimension")

    known = {identity(dimension)}
    frontier = [identity(dimension)]
    steps = tuple(generators)
    while frontier:
        current = frontier.pop()
        for generator in steps:
            candidate = generator.compose(current)
            if candidate in known:
                continue
            known.add(candidate)
            frontier.append(candidate)
            if len(known) > max_order:
                raise RuntimeError(
                    f"affine closure exceeded max_order={max_order}; "
                    "the input may not define a finite reciprocal point action"
                )
    return tuple(sorted(known))


def _smith_decomposition(matrix: sp.Matrix) -> tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    domain_matrix = DomainMatrix.from_Matrix(matrix).convert_to(ZZ)
    normal, left, right = smith_normal_decomp(domain_matrix)
    return normal.to_Matrix(), left.to_Matrix(), right.to_Matrix()


def _smith_left_transform(matrix: sp.Matrix) -> tuple[sp.Matrix, sp.Matrix]:
    normal, left, _right = _smith_decomposition(matrix)
    return normal, left


def torus_solution(
    matrices: Sequence[sp.Matrix], shifts: Sequence[Sequence[Fraction]]
) -> tuple[Fraction, ...] | None:
    """Return one exact theta solving C_i theta = q_i (mod Z), if it exists."""

    if len(matrices) != len(shifts) or not matrices:
        raise ValueError("matrices and shifts must be nonempty and aligned")
    columns = matrices[0].cols
    stacked = matrices[0]
    rhs_values = list(shifts[0])
    for matrix, shift in zip(matrices[1:], shifts[1:]):
        if matrix.cols != columns:
            raise ValueError("all congruence matrices must have the same column count")
        stacked = stacked.col_join(matrix)
        rhs_values.extend(shift)

    normal, left, right = _smith_decomposition(stacked)
    rhs = left * sp.Matrix(
        [sp.Rational(value.numerator, value.denominator) for value in rhs_values]
    )
    rank = 0
    for index in range(min(normal.rows, normal.cols)):
        if normal[index, index] != 0:
            rank += 1
    for row in range(rank, normal.rows):
        value = sp.Rational(rhs[row])
        if value.q != 1:
            return None

    smith_coordinates = sp.zeros(columns, 1)
    for index in range(rank):
        smith_coordinates[index] = sp.Rational(rhs[index]) / normal[index, index]
    theta = right * smith_coordinates
    return tuple(
        Fraction(int(sp.Rational(value).p), int(sp.Rational(value).q)) % 1 for value in theta
    )


def torus_system(
    matrices: Sequence[sp.Matrix], shifts: Sequence[Sequence[Fraction]]
) -> dict:
    """Solve C_i theta = q_i (mod Z) exactly via Smith decomposition.

    Nonzero Smith rows are always solvable because multiplication by a
    nonzero integer is surjective on R/Z.  A zero Smith row is the exact
    obstruction: the corresponding transformed right-hand side must be an
    integer.
    """

    if len(matrices) != len(shifts) or not matrices:
        raise ValueError("matrices and shifts must be nonempty and aligned")
    columns = matrices[0].cols
    if any(matrix.cols != columns for matrix in matrices):
        raise ValueError("all congruence matrices must have the same column count")
    stacked = matrices[0]
    rhs_values = list(shifts[0])
    for matrix, shift in zip(matrices[1:], shifts[1:]):
        stacked = stacked.col_join(matrix)
        rhs_values.extend(shift)

    normal, left = _smith_left_transform(stacked)
    rhs = left * sp.Matrix([sp.Rational(value.numerator, value.denominator) for value in rhs_values])
    zero_rows = [i for i in range(normal.rows) if all(normal[i, j] == 0 for j in range(normal.cols))]
    violations = []
    for row in zero_rows:
        value = sp.Rational(rhs[row])
        if value.q != 1:
            violations.append(
                {
                    "smith_row": row,
                    "left_witness": [int(left[row, j]) for j in range(left.cols)],
                    "pairing_mod_1": rational_json(Fraction(int(value.p), int(value.q)) % 1),
                }
            )
    diagonal = [
        abs(int(normal[i, i]))
        for i in range(min(normal.rows, normal.cols))
        if normal[i, i] != 0
    ]
    return {
        "solvable": not violations,
        "smith_nonzero": diagonal,
        "zero_row_count": len(zero_rows),
        "violations": violations,
    }


def common_origin_test(generators: Sequence[AffineElement]) -> dict:
    dimension = generators[0].dimension
    matrices = [sp.eye(dimension) - sp.Matrix(generator.linear) for generator in generators]
    shifts = [generator.shift for generator in generators]
    result = torus_system(matrices, shifts)
    result["intrinsic_momentum_nonsymmorphic"] = not result["solvable"]
    return result


def fixed_point_test(element: AffineElement) -> dict:
    dimension = element.dimension
    return torus_system([sp.eye(dimension) - sp.Matrix(element.linear)], [element.shift])


def global_fixed_point_test(group: Sequence[AffineElement]) -> dict:
    dimension = group[0].dimension
    matrices = [sp.eye(dimension) - sp.Matrix(element.linear) for element in group]
    shifts = [element.shift for element in group]
    return torus_system(matrices, shifts)


def parse_generator(raw: dict, dimension: int) -> tuple[str, AffineElement, dict]:
    name = str(raw["name"])
    spatial = matrix_from_tuple(raw["M"])
    if spatial.rows != dimension or abs(int(spatial.det())) != 1:
        raise ValueError(f"{name}: M must be a {dimension}D unimodular integer matrix")
    grading = int(raw.get("s", 1))
    if grading not in (-1, 1):
        raise ValueError(f"{name}: s must be +1 or -1")
    reciprocal = grading * spatial.inv().T
    if "Q" in raw:
        shift = qtuple(raw["Q"])
        shift_source = "Q"
    elif "kappa" in raw:
        shift = qtuple([frac(value) / 2 for value in raw["kappa"]])
        shift_source = "Q=kappa/2"
    else:
        raise ValueError(f"{name}: either Q or kappa is required")
    element = AffineElement(matrix_tuple(reciprocal), shift)
    if element.dimension != dimension:
        raise ValueError(f"{name}: Q has wrong dimension")
    metadata = {
        "name": name,
        "M": [list(map(int, spatial.row(i))) for i in range(dimension)],
        "s": grading,
        "shift_source": shift_source,
        **element.as_json(),
    }
    return name, element, metadata


def group_fingerprint(group: Sequence[AffineElement]) -> str:
    serial = json.dumps([element.as_json() for element in group], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serial.encode("ascii")).hexdigest()


def enumerate_record(raw: dict, max_order: int) -> dict:
    record_id = str(raw["id"])
    if raw.get("status") == "BLOCKED_MISSING_GENERATORS" or not raw.get("generators"):
        return {
            "id": record_id,
            "parent_sg": raw.get("parent_sg"),
            "status": "BLOCKED_MISSING_GENERATORS",
            "reason": raw.get("reason", "generator-level M, s, and Q data are required"),
        }

    dimension = int(raw.get("dimension", 3))
    parsed = [parse_generator(generator, dimension) for generator in raw["generators"]]
    elements = [item[1] for item in parsed]
    group = close_affine_group(elements, max_order=max_order)
    nonidentity = [element for element in group if element != identity(dimension)]
    fixed = [fixed_point_test(element) for element in nonidentity]
    element_diagnostics = []
    for element, result in zip(nonidentity, fixed):
        matrix = sp.Matrix(element.linear)
        element_diagnostics.append(
            {
                **element.as_json(),
                "det_A": int(matrix.det()),
                "has_fixed_point": result["solvable"],
                "fixed_point_obstruction": result["violations"],
            }
        )
    linear_parts = {element.linear for element in group}
    fractional_kernel = [
        element.as_json()
        for element in group
        if element.linear == identity(dimension).linear and element.shift != identity(dimension).shift
    ]
    origin = common_origin_test(elements)
    global_fixed = global_fixed_point_test(group)
    return {
        "id": record_id,
        "parent_sg": raw.get("parent_sg"),
        "status": "COMPLETE",
        "dimension": dimension,
        "input_generators": [item[2] for item in parsed],
        "affine_group_order": len(group),
        "linear_group_order": len(linear_parts),
        "fractional_translation_kernel": fractional_kernel,
        "origin_test": origin,
        "has_global_fixed_point": global_fixed["solvable"],
        "free_action": all(not result["solvable"] for result in fixed),
        "fixed_point_free_element_count": sum(not result["solvable"] for result in fixed),
        "nonidentity_element_count": len(nonidentity),
        "exact_basis_fingerprint": group_fingerprint(group),
        "group_elements": [element.as_json() for element in group],
        "nonidentity_element_diagnostics": element_diagnostics,
        "notes": raw.get("notes", []),
    }


def enumerate_catalog(payload: dict, max_order: int = 4096) -> dict:
    records = [enumerate_record(record, max_order=max_order) for record in payload["records"]]
    complete = [record for record in records if record["status"] == "COMPLETE"]
    blocked = [record for record in records if record["status"] != "COMPLETE"]
    intrinsic = [record for record in complete if record["origin_test"]["intrinsic_momentum_nonsymmorphic"]]
    return {
        "schema_version": 1,
        "convention": "k -> s M^{-T} k + Q on R^d/Z^d; origin removal solves (I-s M^{-T}) theta = Q",
        "input_record_count": len(records),
        "complete_record_count": len(complete),
        "blocked_record_count": len(blocked),
        "intrinsic_momentum_nonsymmorphic_count": len(intrinsic),
        "unique_exact_basis_group_count": len({record["exact_basis_fingerprint"] for record in complete}),
        "scientific_status": (
            "COMPLETE_FOR_INPUT" if not blocked else "PARTIAL_BLOCKED_MISSING_GENERATOR_DATA"
        ),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON file containing generator-level SSG records")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--max-order", type=int, default=4096)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = enumerate_catalog(payload, max_order=args.max_order)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
