Get[FileNameJoin[{DirectoryName[$InputFileName], "SSGReciprocalDatabase", "Kernel", "SSGReciprocalDatabase.wl"}]];
If[SSGReciprocalDatabaseVersion =!= {0, 8, 1}, Exit[1]];
Do[
  result = getSSGReciprocalSpaceGroup[label];
  If[!AssociationQ[result] || result["Status"] =!= "EXACT_MATCH", Exit[2]];
  If[!TrueQ[result["ExactOperationSetEquality"]], Exit[3]];
  Print[{label, result["InternationalNumber"], result["InternationalSymbol"]}],
  {label, {"N143.16.1", "N143.10.1", "N6.9.19", "L1.1.1", "N230.1.1"}}
];
If[getSSGReciprocalSpaceGroup["N143.16.1"]["InternationalNumber"] =!= 143, Exit[4]];
If[getSSGReciprocalSpaceGroup["N6.9.19"]["InternationalNumber"] =!= 7, Exit[5]];
If[!MissingQ[getSSGReciprocalSpaceGroup["invalid"]], Exit[6]];
If[!KeyExistsQ[getSSGReciprocalData["N143.16.1"], "ReciprocalSpaceGroup"], Exit[7]];
Print["Standard space-group package tests: PASS"];
Exit[0];
