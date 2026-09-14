#!/usr/bin/env python3
"""Identify and exactly certify (A,Q,s) as a magnetic space group.

A already equals s M^{-T}. The spglib prime is a color, not another minus
sign on coordinates. Only unprimed identity rotations define the lattice.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
import time
from pathlib import Path

from identify_standard_space_groups import (
    PACKAGE, np, sp, spglib, matrix, vector, encode, lattice_basis,
    mod_vector, torus_solution,
    identify as identify_family,
)


def parse_graded(elements):
    result = []
    for e in elements:
        s = int(e["Grading"])
        if s not in (-1, 1) or bool(e["Antiunitary"]) != (s == -1):
            raise ValueError("Invalid or inconsistent grading")
        result.append((matrix(e["LinearPart"]), vector(e["FractionalTranslation"]), s))
    return result


def fingerprint(elements):
    return hashlib.sha256(str(sorted((tuple(a),mod_vector(q),s) for a,q,s in parse_graded(elements))).encode()).hexdigest()


def standard_operations(uni, hall):
    if uni in (282, 284):
        # The 2.7.0 binary tables give XSG 36 for these two BNS-37 entries.
        # Reconstruct the published magnetic Hall symbols C 2 -2c 1c'
        # and C 2 -2c 1bc' from ordinary Hall 182 instead.
        if hall not in (0, 182):
            raise ValueError("BNS 37.184/37.186 reconstruction requires Hall 182")
        ordinary = spglib.get_symmetry_from_database(182)
        t = sp.Matrix([0, 0 if uni == 282 else sp.Rational(1, 2), sp.Rational(1, 2)])
        base = [(matrix(a.tolist()), vector([float(v) for v in q]))
                for a, q in zip(ordinary["rotations"], ordinary["translations"])]
        return [(a, q, 1) for a, q in base] + [(a, sp.Matrix(mod_vector(q+t)), -1) for a, q in base]
    db = spglib.get_magnetic_symmetry_from_database(uni, hall)
    if db is None:
        raise ValueError("Missing standard magnetic setting")
    return [(matrix(a.tolist()), vector([float(v) for v in q]), 1-2*int(t))
            for a,q,t in zip(db["rotations"],db["translations"],db["time_reversals"])]


def operation_json(a,q,s):
    return {"LinearPart": encode(a), "FractionalTranslation": [encode(v) for v in q],
            "Grading": s, "Antiunitary": s == -1,
            "Seitz": [encode(a),[encode(v) for v in q]], "Prime": s == -1}


def identify(elements, _preconditioned=False, _prefer_unitary=False):
    operations = parse_graded(elements)
    eye = sp.eye(3)
    source_lattice = lattice_basis([eye]+[q for a,q,s in operations if a == eye and s == 1])
    rebase = source_lattice.inv()
    search_set = {(tuple(rebase*a*source_lattice),mod_vector(rebase*q),s) for a,q,s in operations}
    search_ops = [(sp.Matrix(3,3,a),sp.Matrix(q),s) for a,q,s in sorted(search_set)]
    rotations = {tuple(a):a for a,_,_ in search_ops}.values()
    seed_metric = sp.Matrix([[13,2,1],[2,23,3],[1,3,37]])
    metric = sum((a.T*seed_metric*a for a in rotations),sp.zeros(3))
    lattice = np.linalg.cholesky(np.array(metric,dtype=float))
    grey = any(a == eye and mod_vector(q) == (0,0,0) and s == -1 for a,q,s in search_ops)
    seeds = [(0.137123,0.271337,0.389719),(0.191137,0.419231,0.071531),(0.321739,0.113917,0.467113)]
    positions, species, colors = [], [], []
    for index, seed in enumerate(seeds,1):
        seen = set()
        for a,q,s in search_ops:
            key = (tuple(a),mod_vector(q))
            if key in seen:
                if not grey:
                    raise ValueError("Two colors of same geometry without grey identity")
                continue
            seen.add(key)
            positions.append((np.array(a,dtype=float)@seed+np.array(q,dtype=float).ravel())%1)
            species.append(index)
            colors.append(0.0 if grey else float(s))
    # Scalar time-odd colors encode exactly s, with no det(A) axial factor.
    ds = spglib.get_magnetic_symmetry_dataset((lattice,positions,species,colors),is_axial=False,symprec=1e-7)
    if ds is None:
        if _preconditioned:
            raise ValueError("No magnetic candidate after conventional-cell rebasing")
        # Some centered nonstandard settings fail spglib's magnetic matcher.
        # Re-express the same colored group in the known family conventional
        # setting. Ensure its integer periods are UNITARY before enumerating.
        unique = {(tuple(a),mod_vector(q)) for a,q,s in operations if not _prefer_unitary or s == 1}
        family = identify_family([{"LinearPart":encode(sp.Matrix(3,3,a)),
                                   "FractionalTranslation":[encode(v) for v in q]} for a,q in unique])
        b = matrix(family["ConventionalCoordinateMatrix"])
        if any(v.q != 1 for v in source_lattice.inv()*b.inv()):
            b = b/2
        if any(v.q != 1 for v in source_lattice.inv()*b.inv()):
            raise ValueError("Preconditioning cell is not a unitary supercell")
        translations = {(sp.S.Zero,)*3}
        frontier = list(translations)
        while frontier:
            q = sp.Matrix(frontier.pop())
            for j in range(3):
                candidate=mod_vector(q+b[:,j])
                if candidate not in translations:
                    translations.add(candidate)
                    frontier.append(candidate)
            if len(translations)>512:
                raise ValueError("Preconditioning translation closure too large")
        rebased={(tuple(b*a*b.inv()),mod_vector(b*q+sp.Matrix(t)),s)
                 for a,q,s in operations for t in translations}
        try:
            result=identify([operation_json(sp.Matrix(3,3,a),q,s) for a,q,s in sorted(rebased)],True)
        except ValueError:
            if not _prefer_unitary:
                return identify(elements, _prefer_unitary=True)
            return search_standard_candidates(elements)
        c=matrix(result["CoordinateMatrix"])*b
        theta=vector(result["OriginShift"])
        ci=c.inv()
        result.update({"CoordinateMatrix":encode(c),
                       "ConventionalCoordinateMatrix":encode(matrix(result["ConventionalCoordinateMatrix"])*b),
                       "SourceUnitaryTranslationBasis":encode(source_lattice),
                       "SourceFamilyTranslationBasis":encode(lattice_basis([eye]+[q for a,q,s in operations if a == eye])),
                       "InputOperations":elements,
                       "InputToStandardOperations":[{"InputIndex":i+1,"Grading":s,"Antiunitary":s == -1,
                           "StandardOperation":operation_json(c*a*ci,mod_vector(c*q+(eye-c*a*ci)*theta),s)}
                           for i,(a,q,s) in enumerate(operations)]})
        actual={(tuple(c*a*ci),mod_vector(c*q+(eye-c*a*ci)*theta),s) for a,q,s in operations}
        expected={(tuple(a),mod_vector(q),s) for a,q,s in parse_graded(result["StandardPrimitiveOperations"])}
        if actual != expected or lattice_basis([c*source_lattice]) != eye:
            raise ValueError("Preconditioned certificate failed in original coordinates")
        result["CandidatePreconditioning"]="Unitary subgroup conventional cell" if _prefer_unitary else "Family conventional cell"
        return result
    try:
        return certify(elements,int(ds.uni_number),int(ds.hall_number),
                       matrix([[float(v) for v in row] for row in ds.transformation_matrix])*rebase)
    except ValueError:
        if _preconditioned:
            raise
        return search_standard_candidates(elements)


def search_standard_candidates(elements):
    """Fallback: enumerate standard MSG extensions of the identified XSG/FSG."""
    ops=parse_graded(elements)
    permutations=[sp.eye(3)]
    for order in itertools.permutations(range(3)):
        for signs in itertools.product((-1,1),repeat=3):
            m=sp.zeros(3)
            for i,j in enumerate(order):
                m[i,j]=signs[i]
            if m.det()==1 and m not in permutations:
                permutations.append(m)
    for unitary_only in (True,False):
        unique={(tuple(a),mod_vector(q)) for a,q,s in ops if not unitary_only or s==1}
        family=identify_family([{"LinearPart":encode(sp.Matrix(3,3,a)),
                                 "FractionalTranslation":[encode(v) for v in q]} for a,q in unique])
        number=family["InternationalNumber"]
        basis=matrix(family["ConventionalCoordinateMatrix"])
        for uni in range(1,1652):
            kind=spglib.get_magnetic_spacegroup_type(uni)
            if ((kind.type==4) != unitary_only):
                continue
            # Determine the actual unitary subgroup from the standard colored
            # operations instead of assuming the BNS prefix names that subgroup.
            raw=standard_operations(uni,0)
            base={(tuple(a),mod_vector(q)) for a,q,s in raw if not unitary_only or s==1}
            raw_ops=[(sp.Matrix(3,3,a),sp.Matrix(q)) for a,q in base]
            detected=spglib.get_spacegroup_type_from_symmetry(
                np.array([a.tolist() for a,q in raw_ops],dtype=int),
                np.array([list(q) for a,q in raw_ops],dtype=float))
            if detected is None or detected.number!=number:
                continue
            reference=identify_family([{"LinearPart":encode(a),"FractionalTranslation":[encode(v) for v in q]} for a,q in raw_ops])
            std_basis=matrix(reference["ConventionalCoordinateMatrix"])
            for change in permutations:
                try:
                    result=certify(elements,uni,0,std_basis.inv()*change*basis)
                    result["CandidatePreconditioning"]="Standard magnetic candidates + exact coboundary"
                    return result
                except ValueError:
                    continue
    raise ValueError("No exact match among standard magnetic candidates")


def certify(elements,uni,hall,p):
    operations=parse_graded(elements)
    eye=sp.eye(3)
    source_lattice=lattice_basis([eye]+[q for a,q,s in operations if a==eye and s==1])
    std_ops = standard_operations(uni,hall)
    h = lattice_basis([eye]+[q for a,q,s in std_ops if a == eye and s == 1])
    hi = h.inv()
    c = hi*p
    ci = c.inv()
    if lattice_basis([c*source_lattice]) != eye:
        raise ValueError("Unitary translation lattice mismatch")
    targets = {}
    for a,q,s in std_ops:
        key, qr = (tuple(hi*a*h),s), mod_vector(hi*q)
        if key in targets and targets[key] != qr:
            raise ValueError("Incomplete standard unitary translation lattice")
        targets[key] = qr
    equations, rhs = [], []
    for a,q,s in operations:
        ar = c*a*ci
        key = (tuple(ar),s)
        if key not in targets:
            raise ValueError("Colored point operation mismatch")
        equations.append(eye-ar)
        rhs.append([Fraction(v) for v in sp.Matrix(targets[key])-c*q])
    solution = torus_solution(equations,rhs)
    if solution is None:
        raise ValueError("Magnetic common coboundary has no solution")
    theta = sp.Matrix([sp.Rational(v) for v in solution])
    actual = {(tuple(c*a*ci),mod_vector(c*q+(eye-c*a*ci)*theta),s) for a,q,s in operations}
    expected = {(a,q,s) for (a,s),q in targets.items()}
    if actual != expected:
        raise ValueError("Exact magnetic operation set mismatch")
    kind = spglib.get_magnetic_spacegroup_type(uni)
    return {
        "Status":"EXACT_MATCH", "UNINumber":uni, "BNSNumber":kind.bns_number,
        "StandardOperationsSource":("Published magnetic Hall generators + ordinary Hall 182"
            if uni in (282,284) else "spglib magnetic symmetry database"),
        "StandardOperationsReference":("https://github.com/spglib/spglib/blob/develop/database/msg/magnetic_hall_symbols.yaml"
            if uni in (282,284) else "https://spglib.readthedocs.io/en/stable/api/python-api.html#spglib.get_magnetic_symmetry_from_database"),
        "OGNumber":kind.og_number, "LitvinNumber":int(kind.litvin_number),
        "MagneticType":int(kind.type), "ReferenceSpaceGroupNumber":int(kind.number),
        "ReferenceHallNumber":hall,
        "ReferenceHallRole":"MaximalUnitarySubgroup" if kind.type == 4 else "FamilySpaceGroup",
        "SourceUnitaryTranslationBasis":encode(source_lattice),
        "SourceFamilyTranslationBasis":encode(lattice_basis([eye]+[q for a,q,s in operations if a == eye])),
        "StandardUnitaryPrimitiveBasis":encode(h),
        "CoordinateMatrix":encode(c), "OriginShift":[encode(v) for v in theta],
        "ConventionalCoordinateMatrix":encode(p), "ConventionalOriginShift":[encode(v) for v in h*theta],
        "CoordinateConvention":"k_standard_unitary_primitive = C k_input + theta; s unchanged",
        "ExactUnitaryLatticeEquality":True, "ExactGradedOperationSetEquality":True,
        "StandardPrimitiveOperations":[operation_json(sp.Matrix(3,3,a),q,s) for a,q,s in sorted(expected)],
        "InputOperations":elements,
        "InputToStandardOperations":[{
            "InputIndex":i+1, "Grading":s, "Antiunitary":s == -1,
            "StandardOperation":operation_json(c*a*ci,mod_vector(c*q+(eye-c*a*ci)*theta),s)
        } for i,(a,q,s) in enumerate(operations)],
        "Scope":"Magnetic (colored) reciprocal-coordinate group image, not the full spinor corepresentation. A already contains s; do not multiply it by s again."
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent",type=int)
    ap.add_argument("--retry-failures",action="store_true",help="Retry only recorded failures; preserve successful certificates")
    ap.add_argument("--output",type=Path,default=PACKAGE/"Data/MagneticSpaceGroupIdentification.json")
    args = ap.parse_args()
    start = time.monotonic()
    classes, labels, failures = {}, {}, {}
    counts, types = Counter(), Counter()
    if args.output.exists():
        classes = json.loads(args.output.read_text())["Classes"]
    ordinary = json.loads((PACKAGE/"Data/SpaceGroupIdentification.json").read_text())
    if args.retry_failures:
        data=json.loads(args.output.read_text())
        for label in list(data["Failures"]):
            parent=int(label.split('.')[0][1:])
            record=json.loads((PACKAGE/f"Data/Reciprocal/sg{parent:03d}.json").read_text())["Records"][label]
            try:
                elements=record["GradedReciprocalGroupElements"]
                key=fingerprint(elements)
                cert=classes.get(key) or identify(elements)
                classes[key]=cert
                data["Labels"][label]=key
                old=ordinary["Classes"][ordinary["Labels"][label]]
                data["FamilySpaceGroups"][label]={"InternationalNumber":old["InternationalNumber"],"InternationalSymbol":old["InternationalSymbol"]}
                del data["Failures"][label]
                print(label,cert["BNSNumber"],flush=True)
            except Exception as error:
                data["Failures"][label]=str(error)
                print(label,str(error),flush=True)
        data["Classes"]=classes
        data["BNSCounts"]=dict(Counter(classes[k]["BNSNumber"] for k in data["Labels"].values()))
        data["MagneticTypeCounts"]=dict(Counter(str(classes[k]["MagneticType"]) for k in data["Labels"].values()))
        data["RetryElapsedSeconds"]=time.monotonic()-start
        tmp=args.output.with_suffix('.tmp')
        tmp.write_text(json.dumps(data,separators=(',',':')))
        tmp.replace(args.output)
        if data["Failures"]:
            raise SystemExit(1)
        return
    family = {}
    paths = [PACKAGE/f"Data/Reciprocal/sg{args.parent:03d}.json"] if args.parent else sorted((PACKAGE/"Data/Reciprocal").glob("sg[0-9][0-9][0-9].json"))
    for path in paths:
        for label, record in json.loads(path.read_text())["Records"].items():
            try:
                elements = record["GradedReciprocalGroupElements"]
                key = fingerprint(elements)
                if key not in classes:
                    classes[key] = identify(elements)
                labels[label] = key
                counts[classes[key]["BNSNumber"]] += 1
                types[str(classes[key]["MagneticType"])] += 1
                old = ordinary["Classes"][ordinary["Labels"][label]]
                family[label] = {"InternationalNumber":old["InternationalNumber"],"InternationalSymbol":old["InternationalSymbol"]}
            except Exception as error:
                failures[label] = str(error)
        payload = {"SchemaVersion":1,"Labels":labels,"Classes":classes,"FamilySpaceGroups":family,
                   "BNSCounts":dict(counts),"MagneticTypeCounts":dict(types),"Failures":failures,
                   "ElapsedSeconds":time.monotonic()-start,"SpglibVersion":spglib.__version__,
                   "Source":"https://spglib.readthedocs.io/en/stable/magnetic_dataset.html"}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        tmp=args.output.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload,separators=(",",":")))
        tmp.replace(args.output)
        print(f"{path.stem}: matched={len(labels)} certificates={len(classes)} failures={len(failures)}",flush=True)
    print(json.dumps({"Records":len(labels),"MagneticGroups":len(counts),"Types":dict(types),"Failures":len(failures),"Seconds":time.monotonic()-start}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
