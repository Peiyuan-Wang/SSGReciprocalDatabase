#!/usr/bin/env python3
"""Audit raw and intrinsic shifts in the noncommuting translation branch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_DATA = HERE / "SSGReciprocalDatabase" / "Data" / "Reciprocal"


def has_raw_shift(record: dict) -> bool:
    return any(
        any(component not in (0, "0") for component in generator.get("Q", []))
        for generator in record.get("GeneratorDerivation", [])
    )


def audit(data_dir: Path) -> dict:
    total = 0
    raw_nonzero = []
    intrinsic = []
    paths = sorted(data_dir.glob("sg*.json"))
    if not paths:
        raise FileNotFoundError(
            f"no reciprocal database shards found under {data_dir}; "
            "pass --data for an installed or extracted complete paclet"
        )
    for path in paths:
        records = json.loads(path.read_text(encoding="utf-8"))["Records"]
        for record in records.values():
            if record.get("TranslationProjectivity") != "noncommuting":
                continue
            total += 1
            if has_raw_shift(record):
                raw_nonzero.append(record["SSGNumber"])
            if record.get("OriginTest", {}).get("intrinsic_momentum_nonsymmorphic"):
                intrinsic.append(record["SSGNumber"])
    return {
        "NoncommutingRecordCount": total,
        "RawNonzeroShiftCount": len(raw_nonzero),
        "RawNonzeroShiftExamples": raw_nonzero[:20],
        "IntrinsicShiftCount": len(intrinsic),
        "IntrinsicShiftExamples": intrinsic[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    result = audit(args.data)
    print(json.dumps(result, indent=2))
    return 1 if result["IntrinsicShiftCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
