#!/usr/bin/env python3
"""Check type-IV database entries against their prescribed unprimed SG type."""
import json
from identify_magnetic_space_groups import PACKAGE, np, spglib, standard_operations


def ordinary_number(rotations, translations):
    result=spglib.get_spacegroup_type_from_symmetry(
        np.array(rotations,dtype=int),np.array(translations,dtype=float))
    return None if result is None else int(result.number)


def main():
    checked=0
    discrepancies=[]
    for uni in range(1,1652):
        kind=spglib.get_magnetic_spacegroup_type(uni)
        if kind.type!=4:
            continue
        checked+=1
        db=spglib.get_magnetic_symmetry_from_database(uni)
        mask=db['time_reversals']==0
        actual=ordinary_number(db['rotations'][mask],db['translations'][mask])
        if actual!=kind.number:
            reconstructed=[(a,q) for a,q,s in standard_operations(uni,0) if s==1]
            corrected=ordinary_number([a.tolist() for a,q in reconstructed],[list(q) for a,q in reconstructed])
            discrepancies.append({'UNI':uni,'BNS':kind.bns_number,'ExpectedUnitarySG':int(kind.number),
                                  'BinaryDatabaseUnitarySG':actual,'ReconstructedUnitarySG':corrected})
            assert corrected==kind.number
    assert all(d['UNI'] in (282,284) for d in discrepancies)
    report={'SpglibVersion':spglib.__version__,'TypeIVEntriesChecked':checked,
            'BinaryDiscrepancies':discrepancies,'Status':'PASS_WITH_DOCUMENTED_RECONSTRUCTION',
            'Reference':'https://github.com/spglib/spglib/blob/develop/database/msg/magnetic_hall_symbols.yaml'}
    (PACKAGE/'Data/MagneticReferenceAudit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
