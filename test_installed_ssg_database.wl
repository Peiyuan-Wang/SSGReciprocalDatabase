Needs["SSGReciprocalDatabase`"];

status = SSGReciprocalDatabaseStatus[];
labels = SSGReciprocalDatabaseLabels[];
sampleLabels = {"L1.1.1", "N6.9.19", "N123.1.1", "L225.1.1", "N230.1.1"};
sampleRecords = getSSGReciprocalData /@ sampleLabels;

If[Lookup[status, "SchemaVersion"] =!= 2, Exit[1]];
If[SSGReciprocalDatabaseVersion =!= {0, 6, 0}, Exit[1]];
If[Lookup[status, "RecordCount"] =!= 67475, Exit[2]];
If[Lookup[status, "CompleteCount"] =!= 67475, Exit[3]];
If[Length[labels] =!= 67475, Exit[4]];
If[!AllTrue[sampleRecords,
    AssociationQ[#] && Lookup[#, "Status"] === "COMPLETE" &], Exit[5]];
If[getSSGNonsymmorphic["N6.9.19"] =!= True, Exit[6]];
If[Length[SSGGradedReciprocalGroupElements["N6.9.19"]] =!= 2, Exit[7]];
formatted = SSGReciprocalSymmetryTable["N143.10.1"];
If[Head[formatted] =!= Column || !FreeQ[formatted, Missing], Exit[8]];
n143Generators = Lookup[getSSGReciprocalGenTab["N143.10.1"], "Generators"];
If[Lookup[n143Generators, "Name"] =!= {"T1", "T2", "T3", "C3+"}, Exit[9]];
If[Head[showSSGReciprocalGenTab["N143.10.1"]] =!= Column, Exit[10]];

Get["SSGReciprocalDatabase`"];
If[SSGReciprocalDatabaseVersion =!= {0, 6, 0}, Exit[11]];
If[Lookup[getSSGReciprocalGenTab["N143.10.1"]["Generators"], "Name"] =!=
    {"T1", "T2", "T3", "C3+"}, Exit[12]];

Print[<|
  "LoadedFrom" -> FindFile["SSGReciprocalDatabase`"],
  "RecordCount" -> Lookup[status, "RecordCount"],
  "CompleteCount" -> Lookup[status, "CompleteCount"],
  "SampleLabels" -> sampleLabels,
  "N6.9.19Nonsymmorphic" -> getSSGNonsymmorphic["N6.9.19"]
|>];
