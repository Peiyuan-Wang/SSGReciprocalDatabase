#!/usr/bin/env python3
"""Recompute one Xiao SSG reciprocal symmetry group from the ISO-IR source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import sympy as sp

from build_ssg_database import complete_record
from enumerate_parent_sg import DEFAULT_ISO_IR_SOURCE, DEFAULT_XIAO, analyze_ssg_iso_ir


HERE = Path(__file__).resolve().parent
PACKAGE_SOURCE = HERE.parent / "Data" / "XiaoO3RepresentationSource.json"


def parse_parameters(raw: str | None):
    if raw is None:
        return None
    payload = json.loads(raw)
    if not isinstance(payload, list) or any(
        not isinstance(item, list) or len(item) != 3 for item in payload
    ):
        raise ValueError("parameters must be a JSON list of [alpha,beta,gamma] triples")
    return [[sp.sympify(value) for value in item] for item in payload]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ssg")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--alternative", type=int, default=1, help="one-based Xiao alternative")
    parser.add_argument("--parameters-json")
    parser.add_argument(
        "--source", type=Path,
        default=PACKAGE_SOURCE if PACKAGE_SOURCE.exists() else DEFAULT_ISO_IR_SOURCE,
    )
    parser.add_argument("--inventory", type=Path, default=DEFAULT_XIAO)
    parser.add_argument("--raw", action="store_true", help="write the full derivation instead of package schema")
    args = parser.parse_args()
    if args.alternative < 1:
        parser.error("--alternative is one-based and must be positive")

    result = analyze_ssg_iso_ir(
        args.ssg,
        source_path=args.source,
        alternative=args.alternative - 1,
        component_parameters=parse_parameters(args.parameters_json),
        inventory_path=args.inventory,
    )
    if args.raw:
        output = result
    else:
        source_record = json.loads(args.source.read_text(encoding="utf-8"))["XiaoRecords"][args.ssg]
        inventory = {
            "id": args.ssg,
            "parent_sg": source_record["ParentSpaceGroup"],
            "magnetic_order": source_record["MagneticOrder"],
            "xiao_table_nonsymmorphic": result.get("xiao_table_nonsymmorphic", False),
        }
        output = complete_record(result, inventory)
        output["DataSource"] = "Official ISO-IR PIR matrices and Xiao O(3) class archive"
        output["Alternative"] = args.alternative
        output["DerivedSchemaVersion"] = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "SSGNumber": args.ssg,
        "Status": output.get("Status", output.get("status")),
        "Output": str(args.output),
    }))


if __name__ == "__main__":
    main()
