#!/usr/bin/env python3
"""Replay exact standard-group certificates and bind every label to its source."""
import json
from pathlib import Path
import time
import sympy as sp
from identify_standard_space_groups import PACKAGE, parse, matrix, vector, lattice_basis, mod_vector, fingerprint, spglib


def verify(certificate):
    eye = sp.eye(3)
    operations = parse(certificate["InputOperations"])
    c = matrix(certificate["CoordinateMatrix"])
    theta = vector(certificate["OriginShift"])
    h = matrix(certificate["StandardPrimitiveBasis"])
    ci, hi = c.inv(), h.inv()
    database = spglib.get_symmetry_from_database(certificate["HallNumber"])
    standard = [(matrix(a.tolist()), vector([float(v) for v in q]))
                for a,q in zip(database["rotations"], database["translations"])]
    assert h == lattice_basis([eye] + [q for a,q in standard if a == eye])
    source = lattice_basis([eye] + [q for a,q in operations if a == eye])
    assert source == matrix(certificate["SourceTranslationBasis"])
    assert lattice_basis([c*source]) == eye
    actual = {(tuple(c*a*ci), mod_vector(c*q+(eye-c*a*ci)*theta)) for a,q in operations}
    expected = {(tuple(hi*a*h), mod_vector(hi*q)) for a,q in standard}
    assert actual == expected, "Full transformed group differs from standard database"
    assert expected == {(tuple(a),mod_vector(q)) for a,q in parse(certificate["StandardPrimitiveOperations"])}
    kind = spglib.get_spacegroup_type(certificate["HallNumber"])
    assert kind.number == certificate["InternationalNumber"]
    assert kind.arithmetic_crystal_class_number == certificate["ArithmeticCrystalClassNumber"]


def main():
    start = time.monotonic()
    path = PACKAGE/"Data/SpaceGroupIdentification.json"
    data = json.loads(path.read_text())
    for key, certificate in data["Classes"].items():
        assert key == fingerprint(certificate["InputOperations"])
        verify(certificate)
    checked = set()
    for shard in sorted((PACKAGE/"Data/Reciprocal").glob("sg[0-9][0-9][0-9].json")):
        for label, record in json.loads(shard.read_text())["Records"].items():
            assert data["Labels"][label] == fingerprint(record["ReciprocalMomentumGroupElements"])
            checked.add(label)
    assert checked == set(data["Labels"])
    assert not data["Failures"]
    report = {"Status": "PASS", "Records": len(checked), "Certificates": len(data["Classes"]),
              "ElapsedSeconds": time.monotonic()-start,
              "Scope": "Exact equality with spglib standard Seitz data and source-label binding; not a new verification of underlying O3 lifts"}
    (path.parent/"SpaceGroupIdentificationValidation.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
