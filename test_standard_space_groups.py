import copy
import unittest
from identify_standard_space_groups import identify
from validate_space_group_identification import verify


def op(a, q):
    return {"LinearPart": a, "FractionalTranslation": q}


I = [[1,0,0],[0,1,0],[0,0,1]]
M = [[1,0,0],[0,-1,0],[0,0,1]]


class StandardGroupsTest(unittest.TestCase):
    def test_mirror_vs_glide(self):
        mirror = identify([op(I,[0,0,0]),op(M,[0,0,0])])
        glide = identify([op(I,[0,0,0]),op(M,[0,0,"1/2"])])
        self.assertEqual(mirror["InternationalNumber"],6)
        self.assertEqual(glide["InternationalNumber"],7)
        verify(mirror)
        verify(glide)

    def test_removable_shift(self):
        result = identify([op(I,[0,0,0]),op(M,[0,"1/2",0])])
        self.assertEqual(result["InternationalNumber"],6)
        verify(result)
        damaged = copy.deepcopy(result)
        damaged["OriginShift"] = ["1/7","1/11","1/13"]
        with self.assertRaises(AssertionError):
            verify(damaged)

    def test_extra_translation(self):
        result = identify([op(I,[0,0,0]),op(I,["1/2",0,0])])
        self.assertEqual(result["InternationalNumber"],1)
        self.assertEqual(result["SourceTranslationBasis"],[["1/2",0,0],[0,1,0],[0,0,1]])
        verify(result)


if __name__ == "__main__":
    unittest.main()
