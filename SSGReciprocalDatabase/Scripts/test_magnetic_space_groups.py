import copy
import json
import unittest
from identify_magnetic_space_groups import identify, operation_json, sp, PACKAGE, standard_operations, mod_vector, certify
from validate_magnetic_space_groups import verify


def op(a,q,s):
    return operation_json(sp.Matrix(a),[sp.Rational(v) for v in q],s)


I=sp.eye(3)
M=sp.diag(1,-1,1)


class MagneticGroupsTest(unittest.TestCase):
    def test_published_hall_reconstruction(self):
        for uni in (282,284):
            ops=standard_operations(uni,0)
            keys={(tuple(a),mod_vector(q),s) for a,q,s in ops}
            for a,q,s in ops:
                for b,t,u in ops:
                    self.assertIn((tuple(a*b),mod_vector(q+a*t),s*u),keys)
            # The unprimed twofold has no screw component along z in Ccc2.
            self.assertTrue(all(q[2] % 1 == 0 for a,q,s in ops if s==1 and a==sp.diag(-1,-1,1)))
            verify(certify([operation_json(a,q,s) for a,q,s in ops],uni,0,I))

    def test_centered_type_iv_regressions(self):
        data=json.loads((PACKAGE/'Data/MagneticSpaceGroupIdentification.json').read_text())
        expected={'N65.9.123':'37.186','N65.9.188':'37.184',
                  'N65.9.197':'37.184','N65.9.90':'37.186',
                  'N67.9.108':'37.186','N67.9.166':'37.184',
                  'N67.9.175':'37.184','N67.9.83':'37.186'}
        for label,bns in expected.items():
            cert=data['Classes'][data['Labels'][label]]
            self.assertEqual(cert['BNSNumber'],bns)
            verify(cert)

    def test_four_types(self):
        groups=[
            [op(I,[0,0,0],1)],
            [op(I,[0,0,0],1),op(I,[0,0,0],-1)],
            [op(I,[0,0,0],1),op(M,[0,0,0],-1)],
            [op(I,[0,0,0],1),op(I,["1/2",0,0],-1)],
        ]
        for expected,group in enumerate(groups,1):
            result=identify(group)
            self.assertEqual(result["MagneticType"],expected)
            verify(result)
            if expected==4:
                self.assertEqual(result["SourceUnitaryTranslationBasis"],I.tolist())
                self.assertNotEqual(result["SourceFamilyTranslationBasis"],I.tolist())

    def test_same_geometry_different_prime(self):
        a=identify([op(I,[0,0,0],1),op(M,[0,0,0],1)])
        b=identify([op(I,[0,0,0],1),op(M,[0,0,0],-1)])
        self.assertNotEqual(a["BNSNumber"],b["BNSNumber"])
        self.assertEqual(a["MagneticType"],1)
        self.assertEqual(b["MagneticType"],3)
        verify(a)
        verify(b)
        bad=copy.deepcopy(b)
        bad["InputOperations"][1]["Grading"]=1
        bad["InputOperations"][1]["Antiunitary"]=False
        with self.assertRaises(AssertionError):
            verify(bad)


if __name__ == "__main__":
    unittest.main()
