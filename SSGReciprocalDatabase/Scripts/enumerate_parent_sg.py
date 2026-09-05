#!/usr/bin/env python3
"""Compute reciprocal symmetry groups for one Xiao parent space group.

This program combines Appendix-F SSG labels with generator matrices exported
from SpaceGroupIrep.  It currently handles commensurate L/P/N rows whose
listed irreps are available as exact named-k representations.  Parametric
non-HSP labels are retained with an explicit unsupported status.
"""

from __future__ import annotations

import argparse
import collections
import itertools
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Sequence

import sympy as sp
from sympy.matrices.normalforms import hermite_normal_form
from sympy.parsing.mathematica import parse_mathematica

from enumerate_reciprocal_groups import (
    AffineElement,
    close_affine_group,
    enumerate_record,
    frac,
    mod_one,
    rational_json,
    torus_solution,
    torus_system,
)
from xiao_o3_matrix_source import XiaoO3MatrixSource


HERE = Path(__file__).resolve().parent
DEFAULT_XIAO = HERE / "all_ssg_classes_blocked.json"
DEFAULT_O3 = HERE.parent / "xiao_o3_rep_class" / "AllO3_Rep"
DEFAULT_ISO_IR_SOURCE = (
    HERE / "official_sources" / "iso_ir" / "XiaoO3RepresentationSource.json"
)
WOLFRAM_KERNEL = Path("/Applications/Wolfram.app/Contents/MacOS/WolframKernel")
VENDOR_DIR = HERE / "_vendor"


def normalize_label(label: str) -> str:
    return (
        label.replace("−", "-")
        .replace("＋", "+")
        .replace("Γ", "GM")
        .strip()
    )


def parse_entry(value: str) -> sp.Expr:
    return sp.simplify(parse_mathematica(value))


def parse_matrix(raw: Sequence[Sequence[str]]) -> sp.Matrix:
    return sp.Matrix([[parse_entry(value) for value in row] for row in raw])


def block_diagonal(matrices: Sequence[sp.Matrix]) -> sp.Matrix:
    return sp.diag(*matrices) if matrices else sp.zeros(0)


def is_zero_matrix(matrix: sp.Matrix) -> bool:
    return all(sp.simplify(value) == 0 for value in matrix)


def real_structure_basis(matrices: Sequence[sp.Matrix]) -> sp.Matrix:
    """Find a permutation real structure J and return a J K-fixed basis."""

    dimension = matrices[0].rows
    for permutation in itertools.permutations(range(dimension)):
        jmat = sp.zeros(dimension)
        for column, row in enumerate(permutation):
            jmat[row, column] = 1
        if any(not is_zero_matrix(jmat * matrix.conjugate() - matrix * jmat) for matrix in matrices):
            continue
        if jmat * jmat != sp.eye(dimension) or jmat != jmat.T:
            continue
        columns = []
        visited = set()
        for index in range(dimension):
            if index in visited:
                continue
            partner = permutation[index]
            if partner == index:
                columns.append(sp.eye(dimension).col(index))
                visited.add(index)
            else:
                e_i = sp.eye(dimension).col(index)
                e_j = sp.eye(dimension).col(partner)
                columns.append((e_i + e_j) / sp.sqrt(2))
                columns.append(sp.I * (e_i - e_j) / sp.sqrt(2))
                visited.update((index, partner))
        basis = sp.Matrix.hstack(*columns)
        transformed = [sp.simplify(basis.conjugate().T * matrix * basis) for matrix in matrices]
        if all(all(sp.simplify(sp.im(value)) == 0 for value in matrix) for matrix in transformed):
            return basis
    raise ValueError("no permutation real structure was found for this O(N) direct sum")


def exact_real(matrix: sp.Matrix) -> sp.Matrix:
    result = matrix.applyfunc(lambda value: sp.simplify(sp.re(sp.expand_complex(value))))
    if any(abs(float(sp.N(sp.im(value)))) > 1e-8 for value in matrix):
        raise ValueError("matrix did not become real")
    return result


def determinant_sign(matrix: sp.Matrix) -> int:
    value = complex(sp.N(matrix.det(), 20))
    if abs(value.imag) > 1e-7 or abs(abs(value.real) - 1) > 1e-7:
        raise ValueError(f"O(N) determinant is not +/-1: {value}")
    return 1 if value.real > 0 else -1


def kernel_lattice_mod2(constraints: Sequence[Sequence[int]], dimension: int = 3) -> sp.Matrix:
    allowed = []
    for parity in itertools.product((0, 1), repeat=dimension):
        if all(sum(row[i] * parity[i] for i in range(dimension)) % 2 == 0 for row in constraints):
            allowed.append(sp.Matrix(parity))
    generators = [2 * sp.eye(dimension).col(i) for i in range(dimension)] + allowed
    return hermite_normal_form(sp.Matrix.hstack(*generators))


def center_lattice_from_commutator(commutator: sp.Matrix) -> sp.Matrix:
    """Return the maximal sublattice in the radical of a Z2 commutator form."""

    if commutator.rows != commutator.cols:
        raise ValueError("translation commutator form must be square")
    constraints = [
        [int(commutator[i, j]) % 2 for i in range(commutator.rows)]
        for j in range(commutator.cols)
    ]
    return kernel_lattice_mod2(constraints, commutator.rows)


@dataclass(frozen=True)
class PinElement:
    quaternion: tuple[float, float, float, float]
    antiunitary: int


def qmul(left: Sequence[float], right: Sequence[float]) -> tuple[float, float, float, float]:
    w1, x1, y1, z1 = left
    w2, x2, y2, z2 = right
    return (
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    )


def qscale(sign: float, value: Sequence[float]) -> tuple[float, float, float, float]:
    return tuple(sign * component for component in value)


def qinverse(value: Sequence[float]) -> tuple[float, float, float, float]:
    w, x, y, z = value
    return (w, -x, -y, -z)


def pin_multiply(left: PinElement, right: PinElement) -> PinElement:
    sign = -1.0 if left.antiunitary and right.antiunitary else 1.0
    return PinElement(
        qscale(sign, qmul(left.quaternion, right.quaternion)),
        left.antiunitary ^ right.antiunitary,
    )


def pin_inverse(value: PinElement) -> PinElement:
    inverse = qinverse(value.quaternion)
    if value.antiunitary:
        inverse = qscale(-1.0, inverse)
    return PinElement(inverse, value.antiunitary)


def pin_power(value: PinElement, exponent: int) -> PinElement:
    if exponent < 0:
        return pin_power(pin_inverse(value), -exponent)
    result = PinElement((1.0, 0.0, 0.0, 0.0), 0)
    base = value
    power = exponent
    while power:
        if power & 1:
            result = pin_multiply(result, base)
        base = pin_multiply(base, base)
        power >>= 1
    return result


def normalize_quaternion(value: Sequence[float]) -> tuple[float, float, float, float]:
    norm = math.sqrt(sum(component * component for component in value))
    result = tuple(component / norm for component in value)
    for component in result:
        if abs(component) > 1e-10:
            return qscale(-1.0, result) if component < 0 else result
    return result


def quaternion_from_rotation(rotation: sp.Matrix) -> tuple[float, float, float, float]:
    r = [[float(sp.N(rotation[i, j], 20)) for j in range(3)] for i in range(3)]
    trace = r[0][0] + r[1][1] + r[2][2]
    if trace > 0:
        scale = math.sqrt(trace + 1.0) * 2
        quaternion = (
            0.25 * scale,
            (r[2][1] - r[1][2]) / scale,
            (r[0][2] - r[2][0]) / scale,
            (r[1][0] - r[0][1]) / scale,
        )
    elif r[0][0] > r[1][1] and r[0][0] > r[2][2]:
        scale = math.sqrt(max(0.0, 1.0 + r[0][0] - r[1][1] - r[2][2])) * 2
        quaternion = (
            (r[2][1] - r[1][2]) / scale,
            0.25 * scale,
            (r[0][1] + r[1][0]) / scale,
            (r[0][2] + r[2][0]) / scale,
        )
    elif r[1][1] > r[2][2]:
        scale = math.sqrt(max(0.0, 1.0 + r[1][1] - r[0][0] - r[2][2])) * 2
        quaternion = (
            (r[0][2] - r[2][0]) / scale,
            (r[0][1] + r[1][0]) / scale,
            0.25 * scale,
            (r[1][2] + r[2][1]) / scale,
        )
    else:
        scale = math.sqrt(max(0.0, 1.0 + r[2][2] - r[0][0] - r[1][1])) * 2
        quaternion = (
            (r[1][0] - r[0][1]) / scale,
            (r[0][2] + r[2][0]) / scale,
            (r[1][2] + r[2][1]) / scale,
            0.25 * scale,
        )
    return normalize_quaternion(quaternion)


def embed_o3(matrix: sp.Matrix) -> sp.Matrix:
    if matrix.rows == 3:
        return matrix
    if matrix.rows == 2:
        return sp.diag(matrix, 1)
    if matrix.rows == 1:
        return sp.diag(matrix[0, 0], 1, 1)
    raise ValueError(f"cannot embed O({matrix.rows}) in O(3)")


def embed_coplanar_o3(matrix: sp.Matrix) -> sp.Matrix:
    if matrix.rows != 2:
        raise ValueError(f"expected an O(2) matrix, got O({matrix.rows})")
    return sp.diag(matrix, determinant_sign(matrix))


def pin_lift(o_matrix: sp.Matrix) -> PinElement:
    grading = determinant_sign(o_matrix)
    proper = sp.simplify(grading * o_matrix)
    return PinElement(quaternion_from_rotation(proper), 0 if grading == 1 else 1)


def central_sign(value: PinElement, tolerance: float = 2e-6) -> int:
    if value.antiunitary:
        raise ValueError("expected a unitary central Pin element")
    q = value.quaternion
    if math.sqrt((q[0] - 1) ** 2 + sum(component * component for component in q[1:])) < tolerance:
        return 0
    if math.sqrt((q[0] + 1) ** 2 + sum(component * component for component in q[1:])) < tolerance:
        return 1
    raise ValueError(f"lift ratio is not central: {q}")


def lattice_lift(generators: Sequence[PinElement], coordinates: Sequence[int]) -> PinElement:
    result = PinElement((1.0, 0.0, 0.0, 0.0), 0)
    for generator, exponent in zip(generators, coordinates):
        result = pin_multiply(result, pin_power(generator, int(exponent)))
    return result


def lattice_matrix_product(generators: Sequence[sp.Matrix], coordinates: Sequence[int]) -> sp.Matrix:
    result = sp.eye(generators[0].rows)
    for generator, exponent in zip(generators, coordinates):
        result = sp.simplify(result * generator ** int(exponent))
    return result


def commutator_bit(left: PinElement, right: PinElement) -> int:
    commutator = pin_multiply(
        pin_multiply(pin_multiply(left, right), pin_inverse(left)), pin_inverse(right)
    )
    return central_sign(commutator)


def matrix_json(matrix: sp.Matrix) -> list[list[int]]:
    if any(not value.is_Integer for value in matrix):
        raise ValueError(f"expected an integer matrix, got {matrix}")
    return [[int(matrix[i, j]) for j in range(matrix.cols)] for i in range(matrix.rows)]


def expression_matrix_json(matrix: sp.Matrix) -> list[list[int | str]]:
    result = []
    for i in range(matrix.rows):
        row = []
        for j in range(matrix.cols):
            value = sp.simplify(matrix[i, j])
            row.append(int(value) if value.is_Integer else str(value))
        result.append(row)
    return result


def common_axis(matrices: Sequence[sp.Matrix]) -> sp.Matrix | None:
    nontrivial = [matrix - sp.eye(3) for matrix in matrices if matrix != sp.eye(3)]
    if not nontrivial:
        return None
    stacked = nontrivial[0]
    for matrix in nontrivial[1:]:
        stacked = stacked.col_join(matrix)
    nullspace = stacked.nullspace()
    return nullspace[0] if len(nullspace) == 1 else None


def axis_sign(proper_rotation: sp.Matrix, axis: sp.Matrix | None) -> int | None:
    if axis is None:
        return None
    transformed = sp.simplify(proper_rotation * axis)
    for index, value in enumerate(axis):
        if sp.simplify(value) != 0:
            ratio = sp.simplify(transformed[index] / value)
            if ratio in (-1, 1) and is_zero_matrix(transformed - ratio * axis):
                return int(ratio)
            return None
    return None


def parse_constituents(row: str, available: dict[str, dict], target_dimension: int) -> list[str]:
    normalized = normalize_label(row)
    labels = []
    dimension = 0
    for piece in normalized.split("⊕"):
        token = piece.strip().split()[0]
        if token not in available:
            raise KeyError(token)
        labels.append(token)
        dimension += int(available[token]["dimension"])
        if dimension >= target_dimension:
            break
    if dimension > target_dimension:
        raise ValueError(f"constituents exceed O({target_dimension}): {labels}")
    while dimension < target_dimension:
        labels.append("GM1")
        dimension += int(available["GM1"]["dimension"])
    return labels


def representation_matrices(
    labels: Sequence[str], available: dict[str, dict], generator_count: int
) -> tuple[list[sp.Matrix], sp.Matrix]:
    components = [available[label] for label in labels]
    matrices = []
    for generator_index in range(generator_count):
        matrices.append(
            block_diagonal(
                [parse_matrix(component["matrices"][generator_index]) for component in components]
            )
        )
    basis = real_structure_basis(matrices)
    real_matrices = [exact_real(sp.simplify(basis.conjugate().T * matrix * basis)) for matrix in matrices]
    return real_matrices, basis


def _fraction_from_iso_vector(raw: Sequence[int]) -> sp.Matrix:
    denominator = int(raw[3])
    if denominator == 0:
        raise ValueError(f"invalid homogeneous ISO-IR vector: {raw}")
    return sp.Matrix([sp.Rational(int(raw[index]), denominator) for index in range(3)])


def _seitz_parts(augmented: Sequence[Sequence[int]]) -> tuple[sp.Matrix, sp.Matrix]:
    matrix = sp.Matrix(augmented)
    if matrix.shape != (4, 4) or matrix[3, 3] == 0:
        raise ValueError(f"invalid ISO-IR augmented Seitz matrix: {augmented}")
    denominator = sp.Integer(matrix[3, 3])
    rotation = sp.simplify(matrix[:3, :3] / denominator)
    translation = sp.simplify(matrix[:3, 3] / denominator)
    return rotation, translation


def _matrix_key(matrix: sp.Matrix) -> tuple[tuple[int, ...], ...]:
    if any(not value.is_Integer for value in matrix):
        raise ValueError(f"point matrix is not integral in the primitive basis: {matrix}")
    return tuple(tuple(int(matrix[i, j]) for j in range(matrix.cols)) for i in range(matrix.rows))


def _matrix_group_closure(generators: Sequence[sp.Matrix]) -> set[tuple[tuple[int, ...], ...]]:
    identity = sp.eye(3)
    known = {_matrix_key(identity)}
    frontier = [identity]
    generators_with_inverses = list(generators) + [matrix.inv() for matrix in generators]
    while frontier:
        left = frontier.pop()
        for right in generators_with_inverses:
            product = sp.simplify(left * right)
            key = _matrix_key(product)
            if key not in known:
                known.add(key)
                frontier.append(product)
    return known


def _point_generator_indices(point_matrices: Sequence[sp.Matrix]) -> list[int]:
    """Choose a deterministic generating subset of the ISO-IR point cosets."""

    selected: list[int] = []
    selected_matrices: list[sp.Matrix] = []
    closure = _matrix_group_closure(selected_matrices)
    for index, matrix in enumerate(point_matrices):
        if _matrix_key(matrix) in closure:
            continue
        selected.append(index)
        selected_matrices.append(matrix)
        closure = _matrix_group_closure(selected_matrices)
    all_operations = {_matrix_key(matrix) for matrix in point_matrices}
    if closure != all_operations:
        raise ValueError("selected ISO-IR point representatives do not generate the full point group")
    return selected


def iso_ir_parent_data(
    source: XiaoO3MatrixSource,
    xiao_label: str,
    alternative: int = 0,
    component_parameters: Sequence[Sequence[sp.Expr | float | int]] | None = None,
) -> dict:
    """Adapt one official ISO-IR realization to the primitive parent-lattice basis."""

    record = source.record(xiao_label)
    labels = record["Alternatives"][alternative]["Constituents"]
    pir = source.data["PIRRecords"][f'{record["ParentSpaceGroup"]}:{labels[0]}']
    parameter_regime = "explicit" if component_parameters is not None else "special-k"
    if component_parameters is None:
        # ISO-IR's official PIR_data.f uses 0.11, 0.12, 0.13 as arbitrary
        # values for non-special k.  Exact rationals avoid numerical ambiguity.
        generic = (sp.Rational(11, 100), sp.Rational(3, 25), sp.Rational(13, 100))
        component_parameters = []
        for label in labels:
            pir_component = source.data["PIRRecords"][f'{record["ParentSpaceGroup"]}:{label}']
            component_parameters.append((0, 0, 0) if pir_component["KSpecial"] else generic)
            if not pir_component["KSpecial"]:
                parameter_regime = "generic-nonspecial-k"

    primitive_vectors = [_fraction_from_iso_vector(raw) for raw in pir["PrimitiveTranslations"]]
    primitive_basis = sp.Matrix.hstack(*primitive_vectors)
    generators = []
    rho = []
    for index in range(3):
        generators.append(
            {
                "name": f"T{index + 1}",
                "kind": "translation",
                "seitz_rotation": "E",
                "seitz_translation": expression_matrix_json(primitive_vectors[index]),
                "M_parent": matrix_json(sp.eye(3)),
            }
        )
        rho.append(
            source.primitive_translation_matrix(
                xiao_label, index, alternative, component_parameters
            )
        )

    point_rotations = []
    point_translations = []
    for operator in pir["Operators"]:
        rotation, translation = _seitz_parts(operator["AugmentedMatrix"])
        point_rotations.append(sp.simplify(primitive_basis.inv() * rotation * primitive_basis))
        point_translations.append(sp.simplify(primitive_basis.inv() * translation))
    selected = _point_generator_indices(point_rotations)
    for output_index, operator_index in enumerate(selected, start=1):
        generators.append(
            {
                "name": f"g{output_index}",
                "kind": "space_group_generator",
                "iso_ir_operator_index": operator_index,
                "seitz_rotation": expression_matrix_json(point_rotations[operator_index]),
                "seitz_translation": expression_matrix_json(point_translations[operator_index]),
                "M_parent": matrix_json(point_rotations[operator_index]),
            }
        )
        rho.append(
            source.matrix(
                xiao_label, operator_index, alternative, component_parameters
            )
        )

    return {
        "bravais_lattice": pir["SpaceGroupSymbol"].split()[0][0],
        "primitive_basis_iso_conventional_coordinates": expression_matrix_json(primitive_basis),
        "representation_labels": labels,
        "generators": generators,
        "rho_matrices": rho,
        "parameter_regime": parameter_regime,
        "component_parameters": [
            [str(sp.sympify(value)) for value in triple]
            for triple in component_parameters
        ],
        "source_note": (
            "Xiao O(3) class resolved through official ISO-IR PIR matrices and Seitz "
            "operators; spatial matrices are rebased to primitive direct-lattice coordinates."
        ),
    }


def analyze_ssg(row: dict, parent_data: dict) -> dict:
    order = row["id"][0]
    target_dimension = {"L": 1, "P": 2, "N": 3}[order]
    if "rho_matrices" in parent_data:
        labels = list(parent_data["representation_labels"])
        rho = [sp.Matrix(matrix) for matrix in parent_data["rho_matrices"]]
    else:
        available = {normalize_label(record["label"]): record for record in parent_data["irreps"]}
        try:
            labels = parse_constituents(row["classification_row_raw"], available, target_dimension)
            rho, _basis = representation_matrices(labels, available, len(parent_data["generators"]))
        except (KeyError, ValueError) as error:
            return {
                "id": row["id"],
                "parent_sg": row["parent_sg"],
                "status": "UNSUPPORTED_PARAMETRIC_OR_REALIFICATION",
                "reason": str(error),
                "classification_row_raw": row["classification_row_raw"],
                "xiao_table_nonsymmorphic": row.get("xiao_table_nonsymmorphic", False),
            }

    rho_o3 = [
        embed_coplanar_o3(matrix) if order == "P" else embed_o3(matrix)
        for matrix in rho
    ]
    rho_generator_records = [
        {
            "name": generator["name"],
            "kind": generator["kind"],
            "rho_O3": expression_matrix_json(matrix),
            "det_rho": determinant_sign(matrix),
        }
        for generator, matrix in zip(parent_data["generators"], rho_o3)
    ]
    translation_rho = rho_o3[:3]
    translation_lifts = [pin_lift(matrix) for matrix in translation_rho]
    grading_bits = [lift.antiunitary for lift in translation_lifts]
    unitary_basis = kernel_lattice_mod2([grading_bits] if any(grading_bits) else [], 3)
    unitary_lifts = [
        lattice_lift(translation_lifts, unitary_basis.col(index)) for index in range(3)
    ]
    commutator = sp.zeros(3)
    for i in range(3):
        for j in range(3):
            commutator[i, j] = commutator_bit(unitary_lifts[i], unitary_lifts[j])
    center_basis_in_unitary_coordinates = center_lattice_from_commutator(commutator)
    bloch_basis = hermite_normal_form(unitary_basis * center_basis_in_unitary_coordinates)
    bloch_lifts = [
        lattice_lift(translation_lifts, bloch_basis.col(index)) for index in range(3)
    ]
    bloch_translation_rho = [
        lattice_matrix_product(translation_rho, bloch_basis.col(index)) for index in range(3)
    ]
    spin_axis = sp.Matrix([0, 0, 1]) if order == "P" else common_axis(bloch_translation_rho)

    affine_generators = []
    generator_details = []

    def append_affine_generator(index: int, spatial_parent: sp.Matrix, physical_role: str) -> None:
        generator = parent_data["generators"][index]
        spatial_bloch = sp.simplify(bloch_basis.inv() * spatial_parent * bloch_basis)
        if any(not value.is_Integer for value in spatial_bloch):
            raise ValueError(f"{row['id']}: physical Bloch lattice is not invariant under {generator['name']}")
        point_lift = pin_lift(rho_o3[index])
        inverse_spatial = spatial_bloch.inv()
        kappa = []
        for lattice_index in range(3):
            conjugated = pin_multiply(
                pin_multiply(pin_inverse(point_lift), bloch_lifts[lattice_index]), point_lift
            )
            target = lattice_lift(bloch_lifts, inverse_spatial.col(lattice_index))
            ratio = pin_multiply(conjugated, pin_inverse(target))
            kappa.append(central_sign(ratio))
        grading = -1 if point_lift.antiunitary else 1
        proper_spin_rotation = sp.simplify(grading * rho_o3[index])
        eta = axis_sign(proper_spin_rotation, spin_axis)
        affine_generators.append(
            {
                "name": generator["name"],
                "M": matrix_json(spatial_bloch),
                "s": grading,
                "kappa": kappa,
            }
        )
        generator_details.append(
            {
                "name": generator["name"],
                "physical_role": physical_role,
                "seitz_rotation": generator["seitz_rotation"],
                "seitz_translation": generator["seitz_translation"],
                "det_rho": grading,
                "rho_O3": expression_matrix_json(rho_o3[index]),
                "proper_spin_rotation": expression_matrix_json(proper_spin_rotation),
                "eta_g": eta,
                "M_parent": generator["M_parent"],
                "M_bloch": matrix_json(spatial_bloch),
                "kappa": kappa,
                "Q": ["1/2" if value else 0 for value in kappa],
            }
        )

    # A parent translation excluded from T_U remains a coset representative of
    # the full graded SSG.  Its semilinear momentum action must enter the same
    # common-origin system as the point-operation representatives.
    for index in range(3):
        if translation_lifts[index].antiunitary:
            append_affine_generator(index, sp.eye(3), "antiunitary translation coset")

    for index in range(3, len(parent_data["generators"])):
        append_affine_generator(
            index,
            sp.Matrix(parent_data["generators"][index]["M_parent"]),
            "parent point-operation coset",
        )

    if order == "P":
        zeta_o3 = sp.diag(1, 1, -1)
        zeta_lift = pin_lift(zeta_o3)
        zeta_kappa = []
        for lattice_index in range(3):
            conjugated = pin_multiply(
                pin_multiply(pin_inverse(zeta_lift), bloch_lifts[lattice_index]), zeta_lift
            )
            ratio = pin_multiply(conjugated, pin_inverse(bloch_lifts[lattice_index]))
            zeta_kappa.append(central_sign(ratio))
        affine_generators.append(
            {
                "name": "zeta_coplanar",
                "M": matrix_json(sp.eye(3)),
                "s": -1,
                "kappa": zeta_kappa,
            }
        )
        generator_details.append(
            {
                "name": "zeta_coplanar",
                "physical_role": "pure-spin antiunitary completion",
                "det_rho": -1,
                "rho_O3": expression_matrix_json(zeta_o3),
                "proper_spin_rotation": expression_matrix_json(-zeta_o3),
                "M_bloch": matrix_json(sp.eye(3)),
                "kappa": zeta_kappa,
                "Q": ["1/2" if value else 0 for value in zeta_kappa],
            }
        )
    if not affine_generators:
        affine_generators.append(
            {"name": "identity", "M": matrix_json(sp.eye(3)), "s": 1, "kappa": [0, 0, 0]}
        )

    exact_record = {
        "id": row["id"],
        "parent_sg": row["parent_sg"],
        "dimension": 3,
        "generators": affine_generators,
        "notes": [parent_data.get("source_note", "Computed from Xiao labels and SpaceGroupIrep generator matrices.")],
    }
    reciprocal = enumerate_record(exact_record, max_order=4096)
    reciprocal.update(
        {
            "xiao_representation_labels": labels,
            "xiao_table_nonsymmorphic": row.get("xiao_table_nonsymmorphic", False),
            "xiao_dSBZ": row.get("dSBZ"),
            "xiao_dBZ": row.get("dBZ"),
            "rho_on_parent_generators": rho_generator_records,
            "translation_grading_bits_parent_basis": grading_bits,
            "translation_rho_O3_parent_generators": [
                expression_matrix_json(matrix) for matrix in translation_rho
            ],
            "unitary_translation_basis_parent_coordinates": matrix_json(unitary_basis),
            "lift_commutator_on_unitary_basis_mod2": matrix_json(commutator),
            "center_basis_in_unitary_coordinates": matrix_json(
                center_basis_in_unitary_coordinates
            ),
            "physical_bloch_basis_parent_coordinates": matrix_json(bloch_basis),
            "physical_bloch_index": abs(int(bloch_basis.det())),
            "translation_projectivity": (
                "noncommuting" if any(int(value) for value in commutator) else "commuting"
            ),
            "common_spin_axis_real_basis": (
                None if spin_axis is None else [str(sp.simplify(value)) for value in spin_axis]
            ),
            "generator_derivation": generator_details,
            "source_convention": (
                "ISO-IR Miller-Love/CDML and primitive direct-lattice coordinates"
                if "rho_matrices" in parent_data
                else "legacy SpaceGroupIrep export"
            ),
            "parent_primitive_basis_iso_conventional_coordinates": parent_data.get(
                "primitive_basis_iso_conventional_coordinates"
            ),
            "representation_parameter_regime": parent_data.get("parameter_regime"),
            "representation_component_parameters": parent_data.get("component_parameters"),
            "agreement_with_xiao_nonsymmorphic_flag": (
                reciprocal["origin_test"]["intrinsic_momentum_nonsymmorphic"]
                == bool(row.get("xiao_table_nonsymmorphic", False))
            ),
        }
    )
    return reciprocal


def analyze_ssg_iso_ir(
    xiao_label: str,
    source_path: Path = DEFAULT_ISO_IR_SOURCE,
    alternative: int = 0,
    component_parameters: Sequence[Sequence[sp.Expr | float | int]] | None = None,
    inventory_path: Path = DEFAULT_XIAO,
) -> dict:
    """Recompute one Xiao SSG entirely from the official ISO-IR-backed source."""

    source = XiaoO3MatrixSource(source_path)
    source_record = source.record(xiao_label)
    inventory = (
        json.loads(inventory_path.read_text(encoding="utf-8"))["records"]
        if inventory_path is not None and inventory_path.exists()
        else []
    )
    row = next((item for item in inventory if item["id"] == xiao_label), None)
    if row is None:
        row = {
            "id": xiao_label,
            "parent_sg": source_record["ParentSpaceGroup"],
            "classification_row_raw": source_record["AppendixFDisplay"],
            "xiao_table_nonsymmorphic": "×" in source_record["AppendixFDisplay"],
        }
    parent_data = iso_ir_parent_data(
        source,
        xiao_label,
        alternative=alternative,
        component_parameters=component_parameters,
    )
    return analyze_ssg(row, parent_data)


def export_parent(sg_number: int, cache: Path, force: bool = False) -> dict:
    if force or not cache.exists():
        command = [
            str(WOLFRAM_KERNEL),
            "-script",
            str(HERE / "export_parent_irreps.wl"),
            str(sg_number),
            str(cache),
        ]
        subprocess.run(command, check=True)
    return json.loads(cache.read_text(encoding="utf-8"))


def _action_records(record: dict) -> list[dict]:
    actions = []
    for generator in record["input_generators"]:
        actions.append(
            {
                "name": generator["name"],
                "s": int(generator["s"]),
                "A": sp.Matrix(generator["A"]),
                "Q": tuple(mod_one(frac(value)) for value in generator["Q"]),
            }
        )
    return actions


def _linear_signature(action: dict) -> tuple:
    return (
        action["s"],
        tuple(tuple(int(action["A"][i, j]) for j in range(3)) for i in range(3)),
    )


def _compatible_generator_matchings(left: list[dict], right: list[dict]) -> Iterable[tuple[int, ...]]:
    left_groups: dict[tuple, list[int]] = collections.defaultdict(list)
    right_groups: dict[tuple, list[int]] = collections.defaultdict(list)
    for index, action in enumerate(left):
        left_groups[_linear_signature(action)].append(index)
    for index, action in enumerate(right):
        right_groups[_linear_signature(action)].append(index)
    if set(left_groups) != set(right_groups):
        return
    if any(len(left_groups[key]) != len(right_groups[key]) for key in left_groups):
        return
    keys = sorted(left_groups)
    permutation_blocks = [
        list(itertools.permutations(right_groups[key])) for key in keys
    ]
    for choices in itertools.product(*permutation_blocks):
        matching = [-1] * len(left)
        for key, target_indices in zip(keys, choices):
            for left_index, right_index in zip(left_groups[key], target_indices):
                matching[left_index] = right_index
        yield tuple(matching)


def _coboundary_equivalent(left: dict, right: dict) -> bool:
    if left["physical_bloch_basis_parent_coordinates"] != right[
        "physical_bloch_basis_parent_coordinates"
    ]:
        return False
    left_actions = _action_records(left)
    right_actions = _action_records(right)
    if len(left_actions) != len(right_actions):
        return False
    identity_matrix = sp.eye(3)
    for matching in _compatible_generator_matchings(left_actions, right_actions):
        matrices = [identity_matrix - action["A"] for action in left_actions]
        differences = [
            tuple(
                mod_one(value - target)
                for value, target in zip(
                    left_actions[index]["Q"], right_actions[matching[index]]["Q"]
                )
            )
            for index in range(len(left_actions))
        ]
        if torus_system(matrices, differences)["solvable"]:
            return True
    return False


def _shifted_actions(actions: list[dict], theta: Sequence[Fraction]) -> list[dict]:
    theta_vector = sp.Matrix(
        [sp.Rational(value.numerator, value.denominator) for value in theta]
    )
    result = []
    for action in actions:
        correction = (sp.eye(3) - action["A"]) * theta_vector
        shifted = tuple(
            mod_one(value - Fraction(int(sp.Rational(delta).p), int(sp.Rational(delta).q)))
            for value, delta in zip(action["Q"], correction)
        )
        result.append({**action, "Q": shifted})
    return result


def _minimal_shift_representative(record: dict) -> dict:
    actions = _action_records(record)
    identity_matrix = sp.eye(3)
    best: tuple | None = None
    best_payload: dict | None = None
    for requested_zero_count in range(len(actions), -1, -1):
        for indices in itertools.combinations(range(len(actions)), requested_zero_count):
            if indices:
                theta = torus_solution(
                    [identity_matrix - actions[index]["A"] for index in indices],
                    [actions[index]["Q"] for index in indices],
                )
                if theta is None:
                    continue
            else:
                theta = (Fraction(0), Fraction(0), Fraction(0))
            shifted = _shifted_actions(actions, theta)
            zero_count = sum(all(value == 0 for value in action["Q"]) for action in shifted)
            ordered = sorted(
                shifted,
                key=lambda action: (
                    _linear_signature(action),
                    action["Q"],
                    action["name"],
                ),
            )
            score = (
                -zero_count,
                tuple(value for action in ordered for value in action["Q"]),
                tuple(_linear_signature(action) for action in ordered),
            )
            if best is None or score < best:
                best = score
                best_payload = {
                    "origin_shift_theta": [rational_json(value) for value in theta],
                    "nonzero_Q_count": len(actions) - zero_count,
                    "generator_actions": [
                        {
                            "name": action["name"],
                            "s": action["s"],
                            "A": expression_matrix_json(action["A"]),
                            "Q": [rational_json(value) for value in action["Q"]],
                        }
                        for action in ordered
                    ],
                }
        if best_payload is not None and -best[0] >= requested_zero_count:
            break
    if best_payload is None:
        raise RuntimeError(f"failed to construct a minimal-Q representative for {record['id']}")
    return best_payload


def _gl_coordinate_form(
    lattice: Sequence[Sequence[int]],
    representative: dict,
    basis_change: sp.Matrix,
) -> dict:
    """Rewrite one class after B' = B U, hence k' = U^T k."""

    if basis_change.shape != (3, 3) or abs(int(basis_change.det())) != 1:
        raise ValueError("basis_change must lie in GL(3,Z)")
    transformed_actions = []
    reciprocal_change = basis_change.T
    reciprocal_change_inverse = reciprocal_change.inv()
    for action in representative["generator_actions"]:
        linear = reciprocal_change * sp.Matrix(action["A"]) * reciprocal_change_inverse
        shift = reciprocal_change * sp.Matrix([frac(value) for value in action["Q"]])
        transformed_actions.append(
            {
                "name": action["name"],
                "s": action["s"],
                "A": expression_matrix_json(linear),
                "Q": [
                    rational_json(mod_one(Fraction(int(value.p), int(value.q))))
                    for value in map(sp.Rational, shift)
                ],
            }
        )
    transformed_lattice = sp.Matrix(lattice) * basis_change
    return {
        "bloch_lattice_basis_parent_coordinates": matrix_json(transformed_lattice),
        "generator_actions": transformed_actions,
        "basis_change_from_hnf_representative": matrix_json(basis_change),
        "momentum_coordinate_relation": "k_prime = U^T k",
    }


def aggregate_reciprocal_classes(records: Sequence[dict]) -> list[dict]:
    groups: list[list[dict]] = []
    for record in sorted(records, key=lambda item: item["id"]):
        if record.get("status") != "COMPLETE":
            continue
        for members in groups:
            if _coboundary_equivalent(record, members[0]):
                members.append(record)
                break
        else:
            groups.append([record])

    classes = []
    for class_index, members in enumerate(groups, start=1):
        representative = members[0]
        minimal = _minimal_shift_representative(representative)
        lattice = representative["physical_bloch_basis_parent_coordinates"]
        identity = sp.eye(3)
        # A nontrivial orientation-preserving relabeling makes the GL
        # equivalence explicit without changing the embedded sublattice.
        cyclic_basis_change = sp.Matrix([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
        classes.append(
            {
                "class_id": f"R{class_index}",
                "classification_data": "(L_B, {A_g}, [Q])",
                "hnf_representative": {
                    **_gl_coordinate_form(lattice, minimal, identity),
                    "origin_shift_used_to_minimize_Q": minimal["origin_shift_theta"],
                },
                "gl_equivalent_coordinate_form": _gl_coordinate_form(
                    lattice, minimal, cyclic_basis_change
                ),
                "equivalence_statement": (
                    "The second form is the same class under B_prime=B U and "
                    "k_prime=U^T k. Distinct embedded sublattices are compared in "
                    "their HNF representatives before this internal basis relabeling."
                ),
                "xiao_ssg_representations": [
                    {
                        "ssg_label": member["id"],
                        "representation_labels": member["xiao_representation_labels"],
                    }
                    for member in members
                ],
            }
        )
    return classes


def identify_reciprocal_space_group(reciprocal_class: dict) -> dict:
    """Identify the ordinary 3D space-group type of one momentum affine group."""

    if str(VENDOR_DIR) not in sys.path:
        sys.path.insert(0, str(VENDOR_DIR))
    try:
        import numpy as np
        import spglib
    except ImportError as error:
        raise RuntimeError(
            "spglib is required for reciprocal space-group identification; "
            "install it into ssg_reciprocal_catalog/_vendor"
        ) from error

    actions = reciprocal_class["hnf_representative"]["generator_actions"]
    generators = [
        AffineElement(
            tuple(tuple(int(value) for value in row) for row in action["A"]),
            tuple(frac(value) for value in action["Q"]),
        )
        for action in actions
    ]
    affine_group = close_affine_group(generators)
    rotations = np.array([element.linear for element in affine_group], dtype=np.intc)
    translations = np.array(
        [[float(value) for value in element.shift] for element in affine_group],
        dtype=float,
    )
    linear_group = sorted({element.linear for element in affine_group})
    metric = np.zeros((3, 3), dtype=float)
    for linear in linear_group:
        matrix = np.array(linear, dtype=float)
        metric += matrix.T @ matrix
    lattice = np.linalg.cholesky(metric)
    space_group = spglib.get_spacegroup_type_from_symmetry(
        rotations, translations, lattice=lattice, symprec=1e-7
    )
    if space_group is None:
        raise RuntimeError(
            f"spglib could not identify reciprocal class {reciprocal_class['class_id']}"
        )
    return {
        "international_number": int(space_group.number),
        "international_short": space_group.international_short,
        "international_full": space_group.international_full,
        "hall_number": int(space_group.hall_number),
        "hall_symbol": space_group.hall_symbol,
        "setting_choice": space_group.choice,
        "point_group": space_group.pointgroup_international,
    }


def aggregate_by_reciprocal_space_group(reciprocal_classes: Sequence[dict]) -> list[dict]:
    grouped: dict[int, dict] = {}
    for reciprocal_class in reciprocal_classes:
        identification = identify_reciprocal_space_group(reciprocal_class)
        number = identification["international_number"]
        if number not in grouped:
            grouped[number] = {
                "space_group": identification,
                "representative_ssg_resolved_class": reciprocal_class["class_id"],
                "ssg_resolved_realizations": [],
            }
        grouped[number]["ssg_resolved_realizations"].append(
            {
                "ssg_resolved_class": reciprocal_class["class_id"],
                "hnf_representative": reciprocal_class["hnf_representative"],
                "xiao_ssg_representations": reciprocal_class["xiao_ssg_representations"],
            }
        )
    return [grouped[number] for number in sorted(grouped)]


def write_markdown_summary(payload: dict, destination: Path) -> None:
    lines = [
        f"# Reciprocal symmetry catalog for parent SG {payload['parent_sg']}",
        "",
        f"- Bravais lattice: `{payload['bravais_lattice']}`",
        f"- Xiao rows inspected: {payload['record_count']}",
        f"- Exact commuting rows: {payload['complete_count']}",
        f"- SSG-resolved `(L_B,A_g,[Q])` classes: {payload['ssg_resolved_class_count']}",
        f"- Distinct ordinary reciprocal space groups: {payload['reciprocal_space_group_class_count']}",
        "",
        "## Status counts",
        "",
    ]
    lines.extend(f"- `{status}`: {count}" for status, count in payload["status_counts"].items())
    lines.extend(
        [
            "",
            "## Ordinary reciprocal space-group quotient",
            "",
            "| SG No. | International symbol | Hall symbol | SSG-resolved realizations |",
            "|---:|---|---|---|",
        ]
    )
    for record in payload["reciprocal_space_group_classes"]:
        space_group = record["space_group"]
        realizations = ", ".join(
            realization["ssg_resolved_class"]
            for realization in record["ssg_resolved_realizations"]
        )
        lines.append(
            f"| {space_group['international_number']} | "
            f"`{space_group['international_short']}` | "
            f"`{space_group['hall_symbol']}` | {realizations} |"
        )
    lines.extend(
        [
            "",
            "## Reciprocal symmetry classes",
            "",
            "| Class | Coordinate form | Bloch-lattice basis | Generator actions `(s_g,A_g)` | `[Q]` representative | GL relation | Xiao SSG labels |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for record in payload["reciprocal_symmetry_classes"]:
        labels = ", ".join(
            member["ssg_label"] for member in record["xiao_ssg_representations"]
        )
        for form_name, key in (
            ("HNF representative", "hnf_representative"),
            ("GL-equivalent form", "gl_equivalent_coordinate_form"),
        ):
            form = record[key]
            lattice = str(form["bloch_lattice_basis_parent_coordinates"]).replace(" ", "")
            actions = "<br>".join(
                f"`{action['name']}: s={action['s']}, A={str(action['A']).replace(' ', '')}`"
                for action in form["generator_actions"]
            )
            shifts = "<br>".join(
                f"`{action['name']}: Q={str(action['Q']).replace(' ', '')}`"
                for action in form["generator_actions"]
            )
            if key == "hnf_representative":
                relation = "representative"
                row_labels = labels
            else:
                matrix = str(form["basis_change_from_hnf_representative"]).replace(" ", "")
                relation = f"`U={matrix}; k'=U^T k`"
                row_labels = ""
            lines.append(
                f"| {record['class_id']} | {form_name} | `{lattice}` | "
                f"{actions} | {shifts} | {relation} | {row_labels} |"
            )
    lines.extend(
        [
            "",
            "Classes keep distinct embedded Bloch sublattices, compare the generator-level "
            "`(s_g,A_g)` combinations, and quotient `Q_g` by arbitrary U(1) origin-shift "
            "coboundaries. Each class is printed twice to exhibit an explicit internal "
            "`GL(3,Z)` basis change. "
            "The JSON retains the original `rho(g)`, `kappa_g`, and Smith witnesses. "
            "Unsupported rows remain fail-closed.",
            "",
        ]
    )
    destination.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent_sg", type=int)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument(
        "--markdown",
        type=Path,
        help="summary path (default: the JSON output path with suffix .md)",
    )
    parser.add_argument("--xiao-inventory", type=Path, default=DEFAULT_XIAO)
    parser.add_argument("--cache-dir", type=Path, default=HERE / "parent_irrep_cache")
    parser.add_argument("--order", choices=("P", "N", "all"), default="all")
    parser.add_argument("--force-export", action="store_true")
    parser.add_argument(
        "--database-source-only",
        action="store_true",
        help="skip reciprocal-class aggregation and emit only per-SSG records",
    )
    args = parser.parse_args()
    if not 1 <= args.parent_sg <= 230:
        parser.error("parent_sg must be between 1 and 230")
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    parent_data = export_parent(
        args.parent_sg,
        args.cache_dir / f"sg{args.parent_sg}_irreps.json",
        force=args.force_export,
    )
    inventory = json.loads(args.xiao_inventory.read_text(encoding="utf-8"))["records"]
    prefixes = ("L", "P", "N") if args.order == "all" else (args.order,)
    rows = [
        row for row in inventory
        if row["parent_sg"] == args.parent_sg and row["id"].startswith(prefixes)
    ]
    results = []
    for row in rows:
        try:
            results.append(analyze_ssg(row, parent_data))
        except Exception as error:  # Preserve the row and continue the parent-group audit.
            results.append(
                {
                    "id": row["id"],
                    "parent_sg": args.parent_sg,
                    "status": "COMPUTATION_ERROR",
                    "reason": f"{type(error).__name__}: {error}",
                    "xiao_table_nonsymmorphic": row.get("xiao_table_nonsymmorphic", False),
                }
            )
    complete = [record for record in results if record.get("status") == "COMPLETE"]
    reciprocal_classes = (
        [] if args.database_source_only else aggregate_reciprocal_classes(complete)
    )
    reciprocal_space_groups = (
        []
        if args.database_source_only
        else aggregate_by_reciprocal_space_group(reciprocal_classes)
    )
    public_results = []
    for record in results:
        public = dict(record)
        public.pop("affine_group_order", None)
        public.pop("linear_group_order", None)
        if "origin_test" in public:
            public["origin_test"] = dict(public["origin_test"])
            public["origin_test"].pop("intrinsic_momentum_nonsymmorphic", None)
        public_results.append(public)
    status_counts = collections.Counter(record.get("status", "UNKNOWN") for record in results)
    unsupported_or_error_count = sum(
        count
        for status, count in status_counts.items()
        if status.startswith("UNSUPPORTED_") or status == "COMPUTATION_ERROR"
    )
    payload = {
        "schema_version": 5,
        "parent_sg": args.parent_sg,
        "bravais_lattice": parent_data["bravais_lattice"],
        "record_count": len(results),
        "complete_count": len(complete),
        "ssg_resolved_class_count": len(reciprocal_classes),
        "reciprocal_space_group_class_count": len(reciprocal_space_groups),
        "non_affine_complete_count": len(results) - len(complete),
        "unsupported_or_error_count": unsupported_or_error_count,
        "status_counts": dict(sorted(status_counts.items())),
        "reciprocal_space_group_classes": reciprocal_space_groups,
        "reciprocal_symmetry_classes": reciprocal_classes,
        "records": public_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path = args.markdown or args.output.with_suffix(".md")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    write_markdown_summary(payload, markdown_path)
    print(
        json.dumps(
            {
                key: value
                for key, value in payload.items()
                if key not in {
                    "records",
                    "reciprocal_symmetry_classes",
                    "reciprocal_space_group_classes",
                }
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
