Get[FileNameJoin[{DirectoryName[$InputFileName], "SSGReciprocalDatabase", "Kernel", "SSGReciprocalDatabase.wl"}]];

status = SSGReciprocalDatabaseStatus[];
If[SSGReciprocalDatabaseVersion =!= {0, 6, 2}, Exit[1]];
If[Lookup[status, "RecordCount"] =!= 67475, Exit[1]];
If[Lookup[status, "CompleteCount"] =!= 67475, Exit[2]];
If[Lookup[status, "ComputedParentSpaceGroups"] =!= 230, Exit[3]];
If[Lookup[status, "XiaoNonsymmorphicDisagreementCount"] =!= 0, Exit[4]];
If[Length[SSGReciprocalDatabaseLabels[]] =!= 67475, Exit[5]];
If[getSSGNonsymmorphic["N6.9.19"] =!= True, Exit[5]];
If[getSSGLB["N6.9.19"] =!= IdentityMatrix[3], Exit[6]];
generators = SSGReciprocalGenElem["N6.9.19"];
If[!ListQ[generators] || !AllTrue[generators, AssociationQ], Exit[7]];
requiredGeneratorKeys = {"SpatialPointMatrix", "Grading", "MomentumLinearPart",
  "LinearPart", "FractionalTranslation", "Seitz"};
If[!AllTrue[generators,
    Function[generator, AllTrue[requiredGeneratorKeys, KeyExistsQ[generator, #] &]]],
  Exit[8]];
If[generators[[1, "SpatialPointMatrix"]] =!= DiagonalMatrix[{1, -1, 1}], Exit[9]];
If[generators[[1, "MomentumLinearPart"]] =!= DiagonalMatrix[{1, -1, 1}], Exit[10]];
If[generators[[1, "FractionalTranslation"]] =!= {"1/2", 0, 0}, Exit[11]];
If[Length[SSGReciprocalGroupElements["N6.9.19"]] =!= 2, Exit[12]];
If[Length[SSGGradedReciprocalGroupElements["N6.9.19"]] =!= 2, Exit[13]];

sampleLabels = {"L1.1.1", "N6.9.19", "N123.1.1", "L225.1.1", "N230.1.1"};
sampleRecords = getSSGReciprocalData /@ sampleLabels;
If[!AllTrue[sampleRecords, AssociationQ[#] && Lookup[#, "Status"] === "COMPLETE" &], Exit[14]];
formattedTables = SSGReciprocalSymmetryTable /@
  {"N6.9.19", "N143.10.1", "P6.3.7", "L35.2.3", "L1.1.1"};
If[!AllTrue[formattedTables, Head[#] === Column && FreeQ[#, Missing] &], Exit[15]];
n143TableData = getSSGReciprocalGenTab["N143.10.1"];
n143Generators = Lookup[n143TableData, "Generators"];
If[Lookup[n143Generators, "Name"] =!= {"T1", "T2", "T3", "C3+"}, Exit[16]];
If[!TrueQ[Lookup[n143Generators[[3]], "Antiunitary"]], Exit[17]];
If[Head[showSSGReciprocalGenTab["N143.10.1"]] =!= Column, Exit[18]];
n143Trivial = getSSGReciprocalGenTab["N143.10.1"];
If[n143Trivial["TranslationImageBranch"] =!= "trivial", Exit[19]];
If[!AllTrue[Values[n143Trivial["EtaByGenerator"]], MissingQ], Exit[20]];
n143Axis = getSSGReciprocalGenTab["N143.11.1"];
If[n143Axis["TranslationImageBranch"] =!= "common-axis" ||
    n143Axis["CommonSpinAxis"] =!= {1, 0, 0}, Exit[21]];
n143Noncommuting = getSSGReciprocalGenTab["N143.16.1"];
If[n143Noncommuting["TranslationImageBranch"] =!= "V4/Q8", Exit[22]];
If[!AllTrue[Lookup[n143Noncommuting["Generators"], "HasFractionalShift"], Not], Exit[23]];
If[Lookup[Last[n143Noncommuting["Generators"]], "RawReciprocalSpaceSeitz"][[2]] =!=
    {1/2, 0, 0}, Exit[24]];
If[AnyTrue[Lookup[SSGReciprocalGenElem["N143.16.1"], "FractionalTranslation"],
    # =!= {0, 0, 0} &], Exit[25]];
If[AnyTrue[Lookup[SSGReciprocalGroupElements["N143.16.1"], "FractionalTranslation"],
    # =!= {0, 0, 0} &], Exit[26]];
Print[<|"RecordCount" -> Lookup[status, "RecordCount"],
  "CompleteCount" -> Lookup[status, "CompleteCount"],
  "ParentSpaceGroups" -> Lookup[status, "ComputedParentSpaceGroups"],
  "N6.9.19LB" -> getSSGLB["N6.9.19"],
  "CrossParentSamples" -> sampleLabels|>];
