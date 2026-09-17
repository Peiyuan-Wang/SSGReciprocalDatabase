file = FileNameJoin[{DirectoryName[$InputFileName], "dist", "SSGReciprocalDatabase-0.8.3.paclet"}];
Print["Isolated user base: ", $UserBaseDirectory];
installed = PacletInstall[file];
Print[installed];
If[!MatchQ[installed, _PacletObject], Exit[1]];
Get["SSGReciprocalDatabase`"];
Print["Loaded: ", FindFile["SSGReciprocalDatabase`"]];
If[SSGReciprocalDatabaseVersion =!= {0,8,3}, Exit[2]];
If[!StringStartsQ[FindFile["SSGReciprocalDatabase`"],
    PacletManager`$UserBasePacletsDirectory], Exit[3]];
If[getSSGReciprocalMagneticSpaceGroup["N143.10.1"]["BNSNumber"] =!= "147.15", Exit[4]];
If[getSSGReciprocalMagneticSpaceGroup["N65.9.123"]["BNSNumber"] =!= "37.186", Exit[5]];
If[getSSGReciprocalFamilySpaceGroup["N143.10.1"]["InternationalNumber"] =!= 147, Exit[6]];
If[Head[showSSGReciprocalMagneticGroup["N143.10.1"]] =!= Column, Exit[7]];
rows = First @ Cases[showSSGReciprocalMagneticGroup["N143.10.1"],
  Grid[value_, ___] :> value, Infinity];
If[rows[[1, 1 ;; 4]] =!=
    {"#", "Parent operation", "MSG operation", "Antiunitary"}, Exit[11]];
If[rows[[2 ;;, 2]] =!= {"E", "C3-", "C3+", "C3+", "C3-", "E"}, Exit[12]];
If[rows[[2 ;;, 3]] =!= {"I'", "S6+'", "S6-'", "C3+", "C3-", "E"}, Exit[13]];
If[Head[showSSGReciprocalGenTab["N143.16.1"]] === Missing, Exit[8]];
publicNames = Names["SSGReciprocalDatabase`*"];
If[Length[publicNames] =!= 24, Exit[14]];
If[!AllTrue[publicNames, StringQ[ToExpression[# <> "::usage"]] &], Exit[15]];
Print["PASS: isolated PacletInstall, load, magnetic/family queries and tables"];
Exit[0];
