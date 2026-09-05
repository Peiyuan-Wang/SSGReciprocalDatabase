#!/usr/bin/env python3
"""Build a Xiao-label keyed reciprocal SSG database from parent-group runs."""

from __future__ import annotations

import argparse
import glob
import json
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _fraction(value: object) -> Fraction:
    if isinstance(value, int):
        return Fraction(value)
    return Fraction(str(value))


def _rational(value: Fraction) -> int | str:
    value %= 1
    return value.numerator if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _matrix_product(left, right):
    return tuple(
        tuple(sum(left[i][k] * right[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


def _matrix_vector(matrix, vector):
    return tuple(sum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3))


def close_graded_reciprocal_group(generators: list[dict]) -> list[dict]:
    """Close (s,A,Q), retaining gradings invisible in the momentum action."""

    identity_matrix = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    identity = (1, identity_matrix, (Fraction(0), Fraction(0), Fraction(0)))
    parsed = [
        (
            int(generator["Grading"]),
            tuple(tuple(int(value) for value in row) for row in generator["LinearPart"]),
            tuple(_fraction(value) % 1 for value in generator["FractionalTranslation"]),
        )
        for generator in generators
    ]
    known = {identity}
    frontier = [identity]
    while frontier:
        left_s, left_a, left_q = frontier.pop()
        for right_s, right_a, right_q in parsed:
            linear = _matrix_product(left_a, right_a)
            transformed = _matrix_vector(left_a, right_q)
            shift = tuple((transformed[i] + left_q[i]) % 1 for i in range(3))
            product = (left_s * right_s, linear, shift)
            if product not in known:
                if len(known) >= 8192:
                    raise RuntimeError("graded reciprocal group exceeded order 8192")
                known.add(product)
                frontier.append(product)
    return [
        {
            "Grading": grading,
            "Antiunitary": grading == -1,
            "LinearPart": [list(row) for row in linear],
            "FractionalTranslation": [_rational(value) for value in shift],
            "Seitz": [[list(row) for row in linear], [_rational(value) for value in shift]],
        }
        for grading, linear, shift in sorted(known)
    ]


def upgrade_complete_record(record: dict) -> dict:
    """Add explicit M_g and the closed graded group to a schema-2 record."""

    derivations = {
        item["name"]: item for item in record.get("GeneratorDerivation", [])
    }
    for generator in record.get("ReciprocalGenerators", []):
        detail = derivations.get(generator["Name"], {})
        point_matrix = detail.get("M_bloch")
        if point_matrix is None and generator["Name"] == "identity":
            point_matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if point_matrix is None:
            raise ValueError(f'missing M_bloch for generator {generator["Name"]}')
        generator["SpatialPointMatrix"] = point_matrix
        generator["MomentumLinearPart"] = generator["LinearPart"]
    record["GradedReciprocalGroupElements"] = close_graded_reciprocal_group(
        record.get("ReciprocalGenerators", [])
    )
    record["GradedReciprocalGroupOrder"] = len(record["GradedReciprocalGroupElements"])
    return record


def base_record(row: dict) -> dict:
    return {
        "SSGNumber": row["id"],
        "ParentSpaceGroup": row["parent_sg"],
        "MagneticOrder": row.get("magnetic_order"),
        "Status": "MISSING_GENERATOR_DATA",
        "Nonsymmorphic": bool(row.get("xiao_table_nonsymmorphic", False)),
        "NonsymmorphicSource": "Xiao Appendix F label",
        "LB": None,
        "ReciprocalGenerators": None,
        "Reason": row.get("reason", "Parent-group generator calculation has not been run."),
    }


def complete_record(record: dict, inventory: dict) -> dict:
    output = base_record(inventory)
    output.update(
        {
            "Status": "COMPLETE",
            "Nonsymmorphic": not bool(record["origin_test"]["solvable"]),
            "NonsymmorphicSource": "Exact common-origin Smith test",
            "LB": record["physical_bloch_basis_parent_coordinates"],
            "LBConvention": (
                "Columns generate the center of the unitary translation-lift group "
                "in the parent direct-lattice basis; the matrix is in column HNF."
            ),
            "TranslationProjectivity": record.get("translation_projectivity"),
            "XiaoTableNonsymmorphic": bool(record.get("xiao_table_nonsymmorphic", False)),
            "AgreementWithXiaoNonsymmorphicFlag": record.get(
                "agreement_with_xiao_nonsymmorphic_flag"
            ),
            "OriginTest": record.get("origin_test"),
            "ReciprocalMomentumGroupOrder": record.get("affine_group_order"),
            "UnitaryTranslationBasis": record.get(
                "unitary_translation_basis_parent_coordinates"
            ),
            "CenterBasisInUnitaryCoordinates": record.get(
                "center_basis_in_unitary_coordinates"
            ),
            "TranslationCommutatorMod2": record.get(
                "lift_commutator_on_unitary_basis_mod2"
            ),
            "SourceConvention": record.get("source_convention"),
            "ParentPrimitiveBasisISOConventionalCoordinates": record.get(
                "parent_primitive_basis_iso_conventional_coordinates"
            ),
            "RepresentationLabels": record.get("xiao_representation_labels"),
            "RepresentationParameterRegime": record.get("representation_parameter_regime"),
            "RepresentationComponentParameters": record.get(
                "representation_component_parameters"
            ),
            "GeneratorDerivation": record.get("generator_derivation"),
            "ReciprocalGenerators": [
                {
                    "Name": generator["name"],
                    "Antiunitary": int(generator["s"]) == -1,
                    "Grading": int(generator["s"]),
                    "LinearPart": generator["A"],
                    "FractionalTranslation": generator["Q"],
                    "Seitz": [generator["A"], generator["Q"]],
                }
                for generator in record["input_generators"]
            ],
            "ReciprocalMomentumGroupElements": [
                {
                    "LinearPart": element["A"],
                    "FractionalTranslation": element["Q"],
                    "Seitz": [element["A"], element["Q"]],
                }
                for element in record.get("group_elements", [])
            ],
            "Reason": None,
        }
    )
    return upgrade_complete_record(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory", type=Path, default=HERE / "all_ssg_classes_blocked.json"
    )
    parser.add_argument(
        "--sources",
        default=str(HERE / "sg*_center_database_source.json"),
        help="glob for enumerate_parent_sg JSON outputs",
    )
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    inventory_payload = json.loads(args.inventory.read_text(encoding="utf-8"))
    inventory = {row["id"]: row for row in inventory_payload["records"]}
    records = {label: base_record(row) for label, row in inventory.items()}
    source_files = sorted(Path(path) for path in glob.glob(args.sources))
    complete_count = 0
    for source in source_files:
        payload = json.loads(source.read_text(encoding="utf-8"))
        for record in payload["records"]:
            label = record["id"]
            if label not in inventory:
                continue
            if record.get("status") == "COMPLETE":
                records[label] = complete_record(record, inventory[label])
                complete_count += 1
            else:
                records[label]["Status"] = record.get("status", "UNAVAILABLE")
                records[label]["Reason"] = record.get("reason")

    output = {
        "SchemaVersion": 1,
        "Source": "Xiao et al., Spin Space Groups: Full Classification and Applications",
        "LBDefinition": "Center of the unitary translation-lift group",
        "RecordCount": len(records),
        "CompleteCount": complete_count,
        "SourceFiles": [str(path) for path in source_files],
        "Records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: value for key, value in output.items() if key != "Records"}, indent=2))


if __name__ == "__main__":
    main()
