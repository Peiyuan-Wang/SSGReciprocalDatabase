#!/usr/bin/env python3
"""Validate every stored point-generator matrix against SpaceGroupIrep names."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "SSGReciprocalDatabase" / "Data"
NAME_FILE = DATA / "SpaceGroupIrepRotationNames.json"
RECIPROCAL = DATA / "Reciprocal"
OUTPUT = DATA / "SpaceGroupIrepRotationNameValidation.json"


def matrix_key(matrix):
    return tuple(tuple(row) for row in matrix)


names = json.loads(NAME_FILE.read_text(encoding="utf-8"))
by_lattice = {
    lattice: {matrix_key(item["Matrix"]): item["Name"] for item in entries}
    for lattice, entries in names["Rotations"].items()
}
all_names = {}
for mapping in by_lattice.values():
    all_names.update(mapping)

unique = set()
for shard in sorted(RECIPROCAL.glob("sg[0-9][0-9][0-9].json")):
    payload = json.loads(shard.read_text(encoding="utf-8"))
    parent = int(payload["ParentSpaceGroup"])
    for record in payload["Records"].values():
        for generator in record.get("GeneratorDerivation", []):
            if str(generator.get("name", "")).startswith("g"):
                unique.add((parent, matrix_key(generator["M_parent"])))

direct = 0
fallback = 0
unmatched = []
for parent, matrix in sorted(unique):
    lattice = names["SpaceGroupBravais"][str(parent)]
    if matrix in by_lattice[lattice]:
        direct += 1
    elif matrix in all_names:
        fallback += 1
    else:
        unmatched.append({"ParentSpaceGroup": parent, "Matrix": matrix})

report = {
    "Status": "PASS" if not unmatched else "FAIL",
    "NamingSource": "SpaceGroupIrep rotation-name tables",
    "UniquePointGeneratorMatrices": len(unique),
    "DirectParentBravaisMatches": direct,
    "CompatibleJonesTableFallbackMatches": fallback,
    "UnmatchedCount": len(unmatched),
    "Unmatched": unmatched,
}
OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if not unmatched else 1)
