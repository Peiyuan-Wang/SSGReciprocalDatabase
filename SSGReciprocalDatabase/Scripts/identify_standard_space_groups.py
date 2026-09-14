#!/usr/bin/env python3
"""Identify reciprocal geometric groups; certify the proposed standard setting exactly.

spglib supplies a candidate Hall setting and basis change. Acceptance requires
exact lattice equality and a common coboundary solved by Smith normal form.
The source SSG grading is retained in the original database, not in this name.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent if ROOT.name == "Scripts" else ROOT / "SSGReciprocalDatabase"
sys.path.insert(0, str(ROOT / "_vendor"))
import numpy as np
import spglib
import sympy as sp
from sympy.matrices.normalforms import hermite_normal_form
from enumerate_reciprocal_groups import torus_solution


def rational(x):
    return sp.Rational(str(x)) if not isinstance(x, float) else sp.Rational(Fraction(x).limit_denominator(10000))


def matrix(x):
    return sp.Matrix([[rational(v) for v in row] for row in x])


def vector(x):
    return sp.Matrix([rational(v) for v in x])


def encode(x):
    if isinstance(x, sp.MatrixBase):
        return [[encode(v) for v in row] for row in x.tolist()]
    if isinstance(x, (sp.Rational, sp.Integer)):
        return int(x) if x.q == 1 else str(x)
    return x


def mod_vector(q):
    return tuple(v % 1 for v in q)


def lattice_basis(columns):
    m = sp.Matrix.hstack(*columns)
    denominator = sp.ilcm(*[v.q for v in m])
    return hermite_normal_form((m * denominator).applyfunc(int)) / denominator


def parse(elements):
    return [(matrix(e["LinearPart"]), vector(e["FractionalTranslation"])) for e in elements]


def fingerprint(elements):
    values = sorted((tuple(a), mod_vector(q)) for a, q in parse(elements))
    return hashlib.sha256(str(values).encode()).hexdigest()


def identify(elements):
    operations = parse(elements)
    eye = sp.eye(3)
    source_lattice = lattice_basis([eye] + [q for a, q in operations if a == eye])
    rotations = {tuple(a): a for a, _ in operations}.values()
    metric = sum((a.T * a for a in rotations), sp.zeros(3))
    lattice = np.linalg.cholesky(np.array(metric, dtype=float))
    # Three independent, differently colored generic orbits remove accidental
    # symmetries of a single orbit. Exact equality below rejects any extra ones.
    seeds = [(0.137123, 0.271337, 0.389719), (0.191137, 0.419231, 0.071531),
             (0.321739, 0.113917, 0.467113)]
    positions, species = [], []
    for color, seed in enumerate(seeds, 1):
        for a, q in operations:
            positions.append((np.array(a, dtype=float) @ seed + np.array(q, dtype=float).ravel()) % 1)
            species.append(color)
    dataset = spglib.get_symmetry_dataset((lattice, positions, species), symprec=1e-7)
    if dataset is None:
        raise ValueError("No standard-setting candidate")
    hall = int(dataset.hall_number)
    standard = spglib.get_symmetry_from_database(hall)
    std_ops = [(matrix(a.tolist()), vector([float(v) for v in q]))
               for a, q in zip(standard["rotations"], standard["translations"])]
    h = lattice_basis([eye] + [q for a, q in std_ops if a == eye])
    hi = h.inv()
    # x_std_conventional = P x_input + p; solve p independently by SNF.
    p = matrix([[float(v) for v in row] for row in dataset.transformation_matrix])
    c = hi * p
    if lattice_basis([c * source_lattice]) != eye:
        raise ValueError("Candidate does not map the FULL translation lattice onto Z^3")
    targets = {}
    for a, q in std_ops:
        ar, qr = hi * a * h, mod_vector(hi * q)
        key = tuple(ar)
        if key in targets and targets[key] != qr:
            raise ValueError("Standard primitive translation lattice is incomplete")
        targets[key] = qr
    equations, rhs = [], []
    ci = c.inv()
    for a, q in operations:
        ar = c * a * ci
        if any(v.q != 1 for v in ar) or tuple(ar) not in targets:
            raise ValueError("Candidate point-group conjugacy failed")
        equations.append(eye - ar)
        rhs.append([Fraction(v) for v in (sp.Matrix(targets[tuple(ar)]) - c * q)])
    theta = torus_solution(equations, rhs)
    if theta is None:
        raise ValueError("No common origin coboundary for candidate")
    theta = sp.Matrix([sp.Rational(v) for v in theta])
    transformed = {(tuple(c*a*ci), mod_vector(c*q + (eye-c*a*ci)*theta)) for a,q in operations}
    expected = {(a,q) for a,q in targets.items()}
    if transformed != expected:
        raise ValueError("Exact full operation-set equality failed")
    kind = spglib.get_spacegroup_type(hall)
    return {
        "Status": "EXACT_MATCH", "InternationalNumber": int(kind.number),
        "InternationalSymbol": kind.international_short, "HallNumber": hall,
        "HallSymbol": kind.hall_symbol, "SettingChoice": kind.choice,
        "ArithmeticCrystalClassNumber": int(kind.arithmetic_crystal_class_number),
        "ArithmeticCrystalClassSymbol": kind.arithmetic_crystal_class_symbol,
        "SourceTranslationBasis": encode(source_lattice),
        "StandardPrimitiveBasis": encode(h), "CoordinateMatrix": encode(c),
        "OriginShift": [encode(v) for v in theta],
        "ConventionalCoordinateMatrix": encode(p),
        "ConventionalOriginShift": [encode(v) for v in h*theta],
        "CoordinateConvention": "k_standard_primitive = CoordinateMatrix k_input + OriginShift",
        "ExactLatticeEquality": True, "ExactOperationSetEquality": True,
        "StandardPrimitiveOperations": [
            {"LinearPart": encode(sp.Matrix(3,3,a)), "FractionalTranslation": [encode(v) for v in q]}
            for a,q in sorted(expected)],
        "InputOperations": elements,
        "Scope": "Ordinary geometric space-group image; antiunitary grading and spin representation remain separate"
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=PACKAGE/"Data/Reciprocal")
    ap.add_argument("--output", type=Path, default=PACKAGE/"Data/SpaceGroupIdentification.json")
    ap.add_argument("--parent", type=int)
    args = ap.parse_args()
    start = time.monotonic()
    cache, labels, counts, failures = {}, {}, Counter(), {}
    if args.output.exists():
        cache = json.loads(args.output.read_text())["Classes"]
    paths = [args.data/f"sg{args.parent:03d}.json"] if args.parent else sorted(args.data.glob("sg[0-9][0-9][0-9].json"))
    for path in paths:
        payload = json.loads(path.read_text())
        for label, record in payload["Records"].items():
            elements = record["ReciprocalMomentumGroupElements"]
            key = fingerprint(elements)
            try:
                if key not in cache:
                    cache[key] = identify(elements)
                labels[label] = key
                counts[str(cache[key]["InternationalNumber"])] += 1
            except Exception as error:
                failures[label] = str(error)
        result = {"SchemaVersion": 1, "SpglibVersion": spglib.__version__,
                  "Labels": labels, "Classes": cache, "SpaceGroupCounts": dict(counts),
                  "Failures": failures, "ElapsedSeconds": time.monotonic()-start,
                  "Sources": ["https://spglib.readthedocs.io/en/stable/database.html",
                              "https://lbfm-rwth.github.io/carat/doc/progs/Vector_systems.html"]}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, separators=(",", ":")))
        temporary.replace(args.output)
        print(f"{path.stem}: matched={len(labels)} unique={len(cache)} failures={len(failures)}", flush=True)
    print(json.dumps({"Matched": len(labels), "Types": len(counts), "Failures": len(failures),
                      "ElapsedSeconds": time.monotonic()-start}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
