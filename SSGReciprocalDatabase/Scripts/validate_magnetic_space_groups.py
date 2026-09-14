#!/usr/bin/env python3
"""Replay certificates against standard magnetic Seitz data with every prime."""
import json
import time
from identify_magnetic_space_groups import (
    PACKAGE, sp, spglib, matrix, vector, lattice_basis, mod_vector,
    parse_graded, fingerprint, standard_operations,
)


def verify(cert):
    eye = sp.eye(3)
    ops = parse_graded(cert["InputOperations"])
    c, h = matrix(cert["CoordinateMatrix"]), matrix(cert["StandardUnitaryPrimitiveBasis"])
    theta = vector(cert["OriginShift"])
    ci, hi = c.inv(), h.inv()
    std = standard_operations(cert["UNINumber"],cert["ReferenceHallNumber"])
    assert h == lattice_basis([eye]+[q for a,q,s in std if a == eye and s == 1])
    source = lattice_basis([eye]+[q for a,q,s in ops if a == eye and s == 1])
    assert source == matrix(cert["SourceUnitaryTranslationBasis"])
    assert lattice_basis([c*source]) == eye
    actual = {(tuple(c*a*ci),mod_vector(c*q+(eye-c*a*ci)*theta),s) for a,q,s in ops}
    expected = {(tuple(hi*a*h),mod_vector(hi*q),s) for a,q,s in std}
    assert actual == expected, "Colored full group equality failed"
    assert expected == {(tuple(a),mod_vector(q),s) for a,q,s in parse_graded(cert["StandardPrimitiveOperations"])}
    kind=spglib.get_magnetic_spacegroup_type(cert["UNINumber"])
    assert kind.bns_number == cert["BNSNumber"] and kind.type == cert["MagneticType"]
    for row in cert["InputToStandardOperations"]:
        a,q,s = ops[row["InputIndex"]-1]
        assert row["Grading"] == s and row["Antiunitary"] == (s == -1)
        actual_row = parse_graded([row["StandardOperation"]])[0]
        assert actual_row == (c*a*ci,sp.Matrix(mod_vector(c*q+(eye-c*a*ci)*theta)),s)


def main():
    start=time.monotonic()
    path=PACKAGE/"Data/MagneticSpaceGroupIdentification.json"
    data=json.loads(path.read_text())
    for key,cert in data["Classes"].items():
        assert fingerprint(cert["InputOperations"]) == key
        verify(cert)
    ordinary=json.loads((PACKAGE/"Data/SpaceGroupIdentification.json").read_text())
    checked=set()
    for path in sorted((PACKAGE/"Data/Reciprocal").glob("sg[0-9][0-9][0-9].json")):
        for label,record in json.loads(path.read_text())["Records"].items():
            assert data["Labels"][label] == fingerprint(record["GradedReciprocalGroupElements"])
            uncolored={(tuple(a),mod_vector(q)) for a,q,s in parse_graded(record["GradedReciprocalGroupElements"])}
            family=ordinary["Classes"][ordinary["Labels"][label]]
            assert uncolored == {(tuple(matrix(e["LinearPart"])),mod_vector(vector(e["FractionalTranslation"]))) for e in family["InputOperations"]}
            assert data["FamilySpaceGroups"][label]["InternationalNumber"] == family["InternationalNumber"]
            checked.add(label)
    assert checked == set(data["Labels"]) and not data["Failures"]
    result={"Status":"PASS","Records":len(checked),"Certificates":len(data["Classes"]),
            "MagneticGroupTypes":len(data["BNSCounts"]),"ElapsedSeconds":time.monotonic()-start,
            "Scope":"Exact colored Seitz equality, unitary lattice equality, source bindings and family-group projection"}
    (PACKAGE/"Data/MagneticSpaceGroupIdentificationValidation.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
