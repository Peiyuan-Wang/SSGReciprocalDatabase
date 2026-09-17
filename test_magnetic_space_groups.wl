Get[FileNameJoin[{DirectoryName[$InputFileName], "SSGReciprocalDatabase", "Kernel", "SSGReciprocalDatabase.wl"}]];
tests = {
 VerificationTest[SSGReciprocalDatabaseVersion, {0,8,4}],
 VerificationTest[getSSGReciprocalMagneticSpaceGroup["N143.10.1"]["BNSNumber"], "147.15"],
 VerificationTest[getSSGReciprocalMagneticSpaceGroup["N143.10.1"]["MagneticType"], 3],
 VerificationTest[getSSGReciprocalMagneticSpaceGroup["N143.16.1"]["MagneticType"], 1],
 VerificationTest[getSSGReciprocalMagneticSpaceGroup["N65.9.123"]["BNSNumber"], "37.186"],
 VerificationTest[getSSGReciprocalMagneticSpaceGroup["N65.9.188"]["BNSNumber"], "37.184"],
 VerificationTest[getSSGReciprocalFamilySpaceGroup["N143.10.1"]["InternationalNumber"], 147],
 VerificationTest[Head[showSSGReciprocalMagneticGroup["N143.10.1"]], Column],
 VerificationTest[
  Module[{rows = Last @ Cases[showSSGReciprocalMagneticGroup["N143.10.1"],
      Grid[value_, ___] :> value, Infinity]}, rows[[2 ;;, 2]]],
  {"K1", "K2", "K3", "T3", "C3+"}],
 VerificationTest[
  Module[{rows = Last @ Cases[showSSGReciprocalMagneticGroup["N143.10.1"],
      Grid[value_, ___] :> value, Infinity]}, rows[[2 ;;, 3]]],
  {"t1", "t2", "t3", "I'", "C3+"}],
 VerificationTest[
  Module[{rows = Last @ Cases[showSSGReciprocalMagneticGroup["N143.10.1"],
      Grid[value_, ___] :> value, Infinity]}, rows[[1]]],
  {"#", "SSG generator", "MSG generator", "Antiunitary",
   "Momentum space symmetry of SSG", "Real space symmetry of MSG"}],
 VerificationTest[MissingQ[getSSGReciprocalMagneticSpaceGroup["INVALID"]], True]
};
report = TestReport[tests];
Print[report];
Print["Succeeded: ", report["TestsSucceededCount"], "; failed: ", report["TestsFailedCount"]];
Exit[If[report["TestsFailedCount"] == 0, 0, 1]];
