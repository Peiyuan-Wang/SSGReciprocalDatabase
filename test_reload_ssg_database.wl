Get["SSGReciprocalDatabase`"];
If[SSGReciprocalDatabaseVersion =!= {0, 6, 2}, Exit[1]];

Unprotect @@ Names["SSGReciprocalDatabase`*"];
ClearAll @@ Names["SSGReciprocalDatabase`*"];
ClearAll @@ Names["SSGReciprocalDatabase`Private`*"];
If[OwnValues[SSGReciprocalDatabaseVersion] =!= {}, Exit[2]];

Get["SSGReciprocalDatabase`"];
If[SSGReciprocalDatabaseVersion =!= {0, 6, 2}, Exit[3]];
names = Lookup[getSSGReciprocalGenTab["N143.10.1"]["Generators"], "Name"];
If[names =!= {"T1", "T2", "T3", "C3+"}, Exit[4]];

Get["SSGReciprocalDatabase`"];
If[Head[showSSGReciprocalGenTab["N143.10.1"]] =!= Column, Exit[5]];
Print[<|"ClearAndReload" -> "PASS", "SecondExplicitGet" -> "PASS",
  "N143.10.1Generators" -> names|>];
