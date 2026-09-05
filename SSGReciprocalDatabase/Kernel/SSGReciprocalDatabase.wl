With[{path = DirectoryName[$InputFileName]},
  If[!MemberQ[$Path, path], AppendTo[$Path, path]]
];

BeginPackage["SSGReciprocalDatabase`"]; 

Unprotect @@ Names["SSGReciprocalDatabase`*"];
ClearAll @@ Names["SSGReciprocalDatabase`*"];
ClearAll @@ Names["SSGReciprocalDatabase`Private`*"];

SSGReciprocalDatabaseVersion::usage =
  "SSGReciprocalDatabaseVersion gives the installed package version as {major, minor, patch}.";
SSGReciprocalDatabaseVersion = {0, 6, 0};

getSSGReciprocalData::usage =
  "getSSGReciprocalData[\"N6.9.19\"] returns all available reciprocal-space data for a Xiao SSG number.";
getSSGNonsymmorphic::usage =
  "getSSGNonsymmorphic[ssg] returns True or False.";
getSSGNonsymmorphicInfo::usage =
  "getSSGNonsymmorphicInfo[ssg] returns the value together with its evidence source.";
getSSGLB::usage =
  "getSSGLB[ssg] returns the column-HNF basis matrix of the translation-lift center lattice L_B.";
SSGReciprocalGenElem::usage =
  "SSGReciprocalGenElem[ssg] returns reciprocal Seitz generators with separate linear and fractional-translation parts.";
SSGReciprocalGroupElements::usage =
  "SSGReciprocalGroupElements[ssg] returns the closed reciprocal momentum-action group as Seitz elements (A_g,Q_g).";
SSGGradedReciprocalGroupElements::usage =
  "SSGGradedReciprocalGroupElements[ssg] returns the closed reciprocal group while retaining the unitary/antiunitary grading.";
getSSGReciprocalGenTab::usage =
  "getSSGReciprocalGenTab[ssg] returns all three parent translations and the selected spatial point generators with real- and reciprocal-space Seitz data.";
showSSGReciprocalGenTab::usage =
  "showSSGReciprocalGenTab[ssg] displays an English generator table in the style of SpaceGroupIrep.";
SSGReciprocalSymmetryTable::usage =
  "SSGReciprocalSymmetryTable[ssg] is a compatibility alias for showSSGReciprocalGenTab[ssg].";
SSGReciprocalDatabaseStatus::usage =
  "SSGReciprocalDatabaseStatus[] returns database coverage and source information.";
SSGReciprocalDatabaseLabels::usage =
  "SSGReciprocalDatabaseLabels[] returns all indexed Xiao SSG numbers.";
getSSGO3RepresentationData::usage =
  "getSSGO3RepresentationData[ssg] returns the complete Xiao-to-ISO-IR O(3) representation record.";
getSSGO3RepresentationAlternatives::usage =
  "getSSGO3RepresentationAlternatives[ssg] returns all official ISO-IR representatives of the Xiao equivalence class.";
SSGO3SeitzOperators::usage =
  "SSGO3SeitzOperators[ssg, Alternative -> n] returns the ISO-IR representative Seitz operators.";
SSGO3RepresentationMatrices::usage =
  "SSGO3RepresentationMatrices[ssg, Alternative -> n, Parameters -> p] returns Xiao's exact physical O(1), O(2), or O(3) matrices.";
SSGO3EmbeddedRepresentationMatrices::usage =
  "SSGO3EmbeddedRepresentationMatrices[ssg, opts] embeds Xiao O(1)/O(2)/O(3) matrices uniformly into O(3).";
SSGO3RepresentationDatabaseStatus::usage =
  "SSGO3RepresentationDatabaseStatus[] returns source, convention, and exhaustive-validation metadata.";
SSGRecomputeReciprocalData::usage =
  "SSGRecomputeReciprocalData[ssg] recomputes L_B, s_g, M_g, and Q_g from the official ISO-IR-backed Xiao O(3) source and caches the result.";

Begin["`Private`"];

$databaseDirectory = FileNameJoin[{DirectoryName[$InputFileName], "..", "Data", "Reciprocal"}];
$databaseFile = FileNameJoin[{$databaseDirectory, "metadata.json"}];
$database =.;
$databaseParentCache = <||>;
$o3DatabaseDirectory = FileNameJoin[{DirectoryName[$InputFileName], "..", "Data", "O3"}];
$o3DatabaseFile = FileNameJoin[{$o3DatabaseDirectory, "metadata.json"}];
$o3ValidationFile = FileNameJoin[{DirectoryName[$InputFileName], "..", "Data", "XiaoO3RepresentationValidation.json"}];
$o3MultiplicationValidationFile = FileNameJoin[{DirectoryName[$InputFileName], "..", "Data", "XiaoO3MultiplicationValidation.json"}];
$o3Database =.;
$o3Validation =.;
$o3MultiplicationValidation =.;
$o3ParentCache = <||>;
$derivedCacheDirectory = FileNameJoin[{$UserBaseDirectory, "ApplicationData", "SSGReciprocalDatabase", "Derived"}];
$recomputeScript = FileNameJoin[{DirectoryName[$InputFileName], "..", "Scripts", "recompute_ssg_reciprocal.py"}];
$rotationNameFile = FileNameJoin[{DirectoryName[$InputFileName], "..", "Data", "SpaceGroupIrepRotationNames.json"}];
$rotationNameData =.;

loadDatabase[] := If[!AssociationQ[$database], $database = Import[$databaseFile, "RawJSON"]];
loadDatabaseParent[spaceGroup_Integer] := Module[{key = ToString[spaceGroup], file},
  If[!KeyExistsQ[$databaseParentCache, key],
    file = FileNameJoin[{$databaseDirectory, "sg" <> IntegerString[spaceGroup, 10, 3] <> ".json"}];
    $databaseParentCache[key] = Import[file, "RawJSON"]
  ];
  $databaseParentCache[key]
];
loadO3Database[] := If[!AssociationQ[$o3Database], $o3Database = Import[$o3DatabaseFile, "RawJSON"]];
loadO3Validation[] := If[!AssociationQ[$o3Validation], $o3Validation = Import[$o3ValidationFile, "RawJSON"]];
loadRotationNameData[] := If[!AssociationQ[$rotationNameData],
  $rotationNameData = Import[$rotationNameFile, "RawJSON"]
];
loadO3MultiplicationValidation[] := If[!AssociationQ[$o3MultiplicationValidation],
  $o3MultiplicationValidation = Import[$o3MultiplicationValidationFile, "RawJSON"]
];
loadO3Parent[spaceGroup_Integer] := Module[{key = ToString[spaceGroup], file},
  If[!KeyExistsQ[$o3ParentCache, key],
    file = FileNameJoin[{$o3DatabaseDirectory, "sg" <> IntegerString[spaceGroup, 10, 3] <> ".json"}];
    $o3ParentCache[key] = Import[file, "RawJSON"]
  ];
  $o3ParentCache[key]
];

derivedRecordFile[ssg_String] := FileNameJoin[{$derivedCacheDirectory, ssg <> ".json"}];

lookupRecord[ssg_String] := Module[{records, derived},
  derived = derivedRecordFile[ssg];
  If[FileExistsQ[derived],
    records = Import[derived, "RawJSON"];
    If[Lookup[records, "DerivedSchemaVersion", 0] >= 2, Return[records]]
  ];
  With[{parent = parentFromSSGLabel[ssg]},
    If[MissingQ[parent], Return[parent]];
    records = Lookup[loadDatabaseParent[parent], "Records", <||>]
  ];
  Lookup[records, ssg, Missing["UnknownSSGNumber", ssg]]
];
lookupRecord[ssg_] := Missing["InvalidSSGNumber", ssg];

missingField[record_, field_] := Missing[
  "NotComputed",
  <|"Field" -> field, "Status" -> Lookup[record, "Status", "Unknown"],
    "Reason" -> Lookup[record, "Reason", None]|>
];

getSSGReciprocalData[ssg_] := lookupRecord[ssg];

getSSGNonsymmorphic[ssg_] := Module[{record = lookupRecord[ssg]},
  If[MissingQ[record], record, Lookup[record, "Nonsymmorphic"]]
];

getSSGNonsymmorphicInfo[ssg_] := Module[{record = lookupRecord[ssg]},
  If[MissingQ[record], record,
    <|"Nonsymmorphic" -> Lookup[record, "Nonsymmorphic"],
      "Source" -> Lookup[record, "NonsymmorphicSource"]|>]
];

getSSGLB[ssg_] := Module[{record = lookupRecord[ssg], value},
  If[MissingQ[record], Return[record]];
  value = Lookup[record, "LB", None];
  If[value === None || value === Null, missingField[record, "LB"], value]
];

SSGReciprocalGenElem[ssg_] := Module[{record = lookupRecord[ssg], value},
  If[MissingQ[record], Return[record]];
  value = Lookup[record, "ReciprocalGenerators", None];
  If[value === None || value === Null, missingField[record, "ReciprocalGenerators"], value]
];

SSGReciprocalGroupElements[ssg_] := Module[{record = lookupRecord[ssg], value},
  If[MissingQ[record], Return[record]];
  value = Lookup[record, "ReciprocalMomentumGroupElements", None];
  If[value === None || value === Null,
    missingField[record, "ReciprocalMomentumGroupElements"], value]
];

SSGGradedReciprocalGroupElements[ssg_] := Module[{record = lookupRecord[ssg], value},
  If[MissingQ[record], Return[record]];
  value = Lookup[record, "GradedReciprocalGroupElements", None];
  If[value === None || value === Null,
    missingField[record, "GradedReciprocalGroupElements"], value]
];

SSGReciprocalDatabaseStatus[] := Module[{status, files},
  loadDatabase[];
  status = KeyDrop[$database, {"Labels"}];
  files = If[DirectoryQ[$derivedCacheDirectory], FileNames["*.json", $derivedCacheDirectory], {}];
  Append[status, "ISOIRRecomputedLabels" -> Select[
    FileBaseName /@ files,
    Function[label, Lookup[Import[derivedRecordFile[label], "RawJSON"], "DerivedSchemaVersion", 0] >= 2]
  ]]
];

SSGReciprocalDatabaseLabels[] := Module[{},
  loadDatabase[];
  Lookup[$database, "Labels", {}]
];

Options[SSGRecomputeReciprocalData] = {Alternative -> 1, Parameters -> Automatic};
SSGRecomputeReciprocalData[ssg_String, OptionsPattern[]] := Module[
  {python, alternative, parameters, output, command, result},
  python = SelectFirst[
    {"/Library/Developer/CommandLineTools/usr/bin/python3", "/opt/homebrew/bin/python3",
      "/usr/local/bin/python3", "/usr/bin/python3"},
    FileExistsQ, Missing["PythonNotFound"]
  ];
  If[MissingQ[python], Return[Failure["PythonNotFound", <||>]]];
  If[!FileExistsQ[$recomputeScript],
    Return[Failure["RecomputeScriptNotFound", <|"Path" -> $recomputeScript|>]]
  ];
  alternative = OptionValue[Alternative];
  If[!IntegerQ[alternative] || alternative < 1,
    Return[Failure["InvalidAlternative", <|"Alternative" -> alternative|>]]
  ];
  If[!DirectoryQ[$derivedCacheDirectory],
    CreateDirectory[$derivedCacheDirectory, CreateIntermediateDirectories -> True]
  ];
  output = derivedRecordFile[ssg];
  command = {python, $recomputeScript, ssg, "--alternative", ToString[alternative], "--output", output};
  parameters = OptionValue[Parameters];
  If[parameters =!= Automatic,
    command = Join[command, {"--parameters-json", ExportString[parameters, "RawJSON", "Compact" -> True]}]
  ];
  result = RunProcess[command];
  If[!AssociationQ[result] || Lookup[result, "ExitCode", 1] =!= 0,
    Return[Failure["ReciprocalRecomputeFailed", <|
      "ProcessResult" -> result|>]]
  ];
  Import[output, "RawJSON"]
];
SSGRecomputeReciprocalData[ssg_, OptionsPattern[]] :=
  Failure["InvalidSSGNumber", <|"SSGNumber" -> ssg|>];

parentFromSSGLabel[ssg_String] := Module[{match},
  match = StringSplit[ssg, "."];
  If[Length[match] == 3 && MemberQ[{"L", "P", "N"}, StringTake[First[match], 1]] &&
      StringMatchQ[StringDrop[First[match], 1], DigitCharacter ..],
    FromDigits[StringDrop[First[match], 1]],
    Missing["InvalidSSGNumber", ssg]
  ]
];

lookupO3Record[ssg_String] := Module[{parent, records},
  parent = parentFromSSGLabel[ssg];
  If[MissingQ[parent], Return[parent]];
  records = Lookup[loadO3Parent[parent], "XiaoRecords", <||>];
  Lookup[records, ssg, Missing["UnknownSSGNumber", ssg]]
];
lookupO3Record[ssg_] := Missing["InvalidSSGNumber", ssg];

getSSGO3RepresentationData[ssg_] := lookupO3Record[ssg];

getSSGO3RepresentationAlternatives[ssg_] := Module[{record = lookupO3Record[ssg]},
  If[MissingQ[record], record, Lookup[record, "Alternatives"]]
];

Options[SSGO3SeitzOperators] = {Alternative -> 1};
SSGO3SeitzOperators[ssg_, OptionsPattern[]] := Module[
  {record = lookupO3Record[ssg], alternative, labels, key, pir},
  If[MissingQ[record], Return[record]];
  alternative = OptionValue[Alternative];
  If[!IntegerQ[alternative] || alternative < 1 ||
      alternative > Length[record["Alternatives"]],
    Return[Missing["InvalidAlternative", alternative]]
  ];
  labels = record["Alternatives"][[alternative, "Constituents"]];
  loadO3Database[];
  With[{parentData = loadO3Parent[record["ParentSpaceGroup"]]},
  key = ToString[record["ParentSpaceGroup"]] <> ":" <> First[labels];
  pir = Lookup[parentData["PIRRecords"], key, Missing["MissingPIRRecord", key]]
  ];
  If[MissingQ[pir], pir,
    Join[
      ({
        {#[[4]], 0, 0, #[[1]]},
        {0, #[[4]], 0, #[[2]]},
        {0, 0, #[[4]], #[[3]]},
        {0, 0, 0, #[[4]]}
      } &) /@ pir["PrimitiveTranslations"],
      Lookup[pir["Operators"], "AugmentedMatrix"]
    ]
  ]
];

$o3ExactConstants = {
  0, 1, -1, 1/2, -1/2, 1/4, -1/4,
  Sqrt[3]/2, -Sqrt[3]/2, Sqrt[2]/2, -Sqrt[2]/2,
  Sqrt[3]/4, -Sqrt[3]/4, (Sqrt[3] + 1)/4, -(Sqrt[3] + 1)/4,
  (Sqrt[3] - 1)/4, -(Sqrt[3] - 1)/4,
  (Sqrt[6] + Sqrt[2])/4, -(Sqrt[6] + Sqrt[2])/4,
  (Sqrt[6] - Sqrt[2])/4, -(Sqrt[6] - Sqrt[2])/4,
  Sqrt[6]/4, -Sqrt[6]/4, Sqrt[2]/4, -Sqrt[2]/4
};

blockDiagonal[matrices_List] := Module[{rowSizes, columnSizes},
  If[Length[matrices] == 1, Return[First[matrices]]];
  rowSizes = Length /@ matrices;
  columnSizes = Length[First[#]] & /@ matrices;
  ArrayFlatten@Table[
    If[i == j, matrices[[i]], ConstantArray[0, {rowSizes[[i]], columnSizes[[j]]}]],
    {i, Length[matrices]}, {j, Length[matrices]}
  ]
];

pirTranslationMatrix[pir_, tRaw_List, parameters_List] := Module[
  {dimension, blockCount, blockDimension, translation, t, kRaw, k,
   phase, cosine, sine, start, i, j},
  t = Table[tRaw[[i]]/tRaw[[4]], {i, 3}];
  dimension = pir["Dimension"];
  blockCount = pir["PMKCount"];
  blockDimension = Quotient[dimension, blockCount];
  translation = ConstantArray[0, {dimension, dimension}];
  Do[
    kRaw = pir["KVectors"][[i]];
    k = Table[
      kRaw[[1, j]]/kRaw[[1, 4]] +
        Sum[
          If[kRaw[[m + 1, 4]] == 0, 0,
            parameters[[m]] kRaw[[m + 1, j]]/kRaw[[m + 1, 4]]
          ],
          {m, 3}
        ],
      {j, 3}
    ];
    phase = Simplify[k . t];
    cosine = Cos[2 Pi phase];
    sine = Sin[2 Pi phase];
    start = (i - 1) blockDimension;
    Do[translation[[start + j, start + j]] = cosine, {j, blockDimension}];
    Do[
      translation[[start + j, start + blockDimension/2 + j]] = sine;
      translation[[start + blockDimension/2 + j, start + j]] = -sine,
      {j, blockDimension/2}
    ],
    {i, blockCount}
  ];
  translation
];

pirMatrix[pir_, operatorIndex_Integer, parameters_List] := Module[
  {operator, point},
  operator = pir["Operators"][[operatorIndex]];
  point = Map[$o3ExactConstants[[# + 1]] &, operator["PointMatrixCodes"], {2}];
  If[TrueQ[pir["KSpecial"]], Return[point]];
  Simplify[pirTranslationMatrix[pir, operator["IRTranslation"], parameters] . point]
];

Options[SSGO3RepresentationMatrices] = {Alternative -> 1, Parameters -> Automatic};
SSGO3RepresentationMatrices[ssg_, OptionsPattern[]] := Module[
  {record = lookupO3Record[ssg], alternative, labels, pirRecords, parameters,
   operatorCount},
  If[MissingQ[record], Return[record]];
  alternative = OptionValue[Alternative];
  If[!IntegerQ[alternative] || alternative < 1 ||
      alternative > Length[record["Alternatives"]],
    Return[Missing["InvalidAlternative", alternative]]
  ];
  labels = record["Alternatives"][[alternative, "Constituents"]];
  loadO3Database[];
  pirRecords = Lookup[
    loadO3Parent[record["ParentSpaceGroup"]]["PIRRecords"],
    (ToString[record["ParentSpaceGroup"]] <> ":" <> #) & /@ labels
  ];
  parameters = OptionValue[Parameters];
  If[parameters === Automatic,
    parameters = Table[
      {Subscript[\[Alpha], i], Subscript[\[Beta], i], Subscript[\[Gamma], i]},
      {i, Length[labels]}
    ]
  ];
  If[!MatchQ[parameters, {{_, _, _} ..}] || Length[parameters] != Length[labels],
    Return[Missing["InvalidParameters", parameters]]
  ];
  operatorCount = Length[First[pirRecords]["Operators"]];
  Join[
    Table[
      blockDiagonal[
        MapThread[
          pirTranslationMatrix[#1, #1["PrimitiveTranslations"][[translationIndex]], #2] &,
          {pirRecords, parameters}
        ]
      ],
      {translationIndex, 3}
    ],
    Table[
      blockDiagonal[
        MapThread[pirMatrix[#1, operatorIndex, #2] &, {pirRecords, parameters}]
      ],
      {operatorIndex, operatorCount}
    ]
  ]
];

Options[SSGO3EmbeddedRepresentationMatrices] = Options[SSGO3RepresentationMatrices];
SSGO3EmbeddedRepresentationMatrices[ssg_, OptionsPattern[]] := Module[
  {record = lookupO3Record[ssg], matrices},
  If[MissingQ[record], Return[record]];
  matrices = SSGO3RepresentationMatrices[
    ssg,
    Alternative -> OptionValue[Alternative],
    Parameters -> OptionValue[Parameters]
  ];
  Switch[record["MagneticOrder"],
    "noncoplanar", matrices,
    "coplanar", (ArrayFlatten[{{#, ConstantArray[0, {2, 1}]},
        {ConstantArray[0, {1, 2}], {{Det[#]}}}}] &) /@ matrices,
    "collinear", (DiagonalMatrix[{#[[1, 1]], 1, 1}] &) /@ matrices,
    _, Missing["InvalidMagneticOrder", record["MagneticOrder"]]
  ]
];

SSGO3RepresentationDatabaseStatus[] := Module[{},
  loadO3Database[];
  loadO3Validation[];
  loadO3MultiplicationValidation[];
  <|
    "Convention" -> $o3Database["Convention"],
    "Sources" -> $o3Database["Sources"],
    "XiaoRecordCount" -> $o3Database["XiaoRecordCount"],
    "PIRRecordCount" -> $o3Database["PIRRecordCount"],
    "Validation" -> $o3Validation,
    "MultiplicationValidation" -> $o3MultiplicationValidation
  |>
];

signedIntegerFromString[value_String] := If[StringStartsQ[value, "-"],
  -FromDigits[StringDrop[value, 1]], FromDigits[value]];

exactDisplayValue[value_String] := Module[{parts},
  If[StringMatchQ[value, RegularExpression["^-?[0-9]+/[1-9][0-9]*$"]],
    parts = signedIntegerFromString /@ StringSplit[value, "/"];
    Rational[parts[[1]], parts[[2]]],
    value
  ]
];
exactDisplayValue[value_List] := exactDisplayValue /@ value;
exactDisplayValue[value_] := value;

seitzDisplay[rotation_, translation_] := Module[{r, t},
  r = exactDisplayValue[rotation];
  t = List /@ Flatten[exactDisplayValue[translation]];
  Grid[{{MatrixForm[r], Style[" | ", Bold], MatrixForm[t]}},
    Alignment -> Center, Spacings -> {0.4, 0.2}]
];

nonzeroShiftQ[generator_Association] := AnyTrue[
  Flatten[exactDisplayValue[Lookup[generator, "FractionalTranslation", {0, 0, 0}]]],
  # =!= 0 &
];

rotationNameFromMatrix[parent_Integer, matrix_List] := Module[
  {bravais, rotations, match, fallback, priority},
  loadRotationNameData[];
  bravais = Lookup[$rotationNameData["SpaceGroupBravais"], ToString[parent], Missing[]];
  rotations = Lookup[$rotationNameData["Rotations"], bravais, {}];
  match = SelectFirst[rotations, Lookup[#, "Matrix", None] === matrix &, Missing[]];
  If[AssociationQ[match], Return[match["Name"]]];
  priority = {"CubiPrim", "HexaPrim", "TrigPrim", "TetrPrim", "OrthPrim",
    "MonoPrim", "TricPrim", "CubiBody", "CubiFace", "TetrBody",
    "OrthBase", "OrthBody", "OrthFace", "MonoBase"};
  fallback = SelectFirst[priority,
    Function[lattice,
      AnyTrue[Lookup[$rotationNameData["Rotations"], lattice, {}],
        Lookup[#, "Matrix", None] === matrix &]
    ],
    Missing[]
  ];
  If[MissingQ[fallback], Return[Missing["RotationNameUnavailable", matrix]]];
  match = SelectFirst[$rotationNameData["Rotations"][fallback],
    Lookup[#, "Matrix", None] === matrix &, Missing[]];
  If[AssociationQ[match], match["Name"], Missing["RotationNameUnavailable", matrix]]
];

notApplicableEta[] := Missing["NotApplicable", "NoUniqueCommonSpinAxis"];

getSSGReciprocalGenTab[ssg_String] := Module[
  {record, reciprocalGenerators, reciprocalByName, derivations, derivationByName,
   pointAndSpinNames, pointAndSpinGenerators, translations, generators, lb,
   reciprocalBasis, latticeIndex, axisDefined, parent, makeTranslation,
   makePointOrSpin},
  record = lookupRecord[ssg];
  If[MissingQ[record], Return[record]];
  If[Lookup[record, "Status", None] =!= "COMPLETE",
    Return[missingField[record, "ReciprocalGeneratorTable"]]
  ];
  parent = Lookup[record, "ParentSpaceGroup"];
  reciprocalGenerators = Lookup[record, "ReciprocalGenerators", {}];
  reciprocalByName = Association[
    (Lookup[#, "Name", ""] -> #) & /@ reciprocalGenerators
  ];
  derivations = Lookup[record, "GeneratorDerivation", {}];
  derivationByName = Association[
    (Lookup[#, "name", ""] -> #) & /@ derivations
  ];
  axisDefined = Lookup[record, "MagneticOrder", ""] === "coplanar" ||
    AnyTrue[Lookup[derivations, "eta_g", None], MemberQ[{-1, 1}, #] &];
  lb = exactDisplayValue[Lookup[record, "LB"]];
  reciprocalBasis = Transpose[Inverse[lb]];
  latticeIndex = Abs[Det[lb]];

  makeTranslation[index_Integer] := Module[
    {internalName, reciprocal, detail, antiunitary, grading, linear, shift, eta},
    internalName = "T" <> ToString[index];
    reciprocal = Lookup[reciprocalByName, internalName, <||>];
    detail = Lookup[derivationByName, internalName, <||>];
    antiunitary = TrueQ[Lookup[reciprocal, "Antiunitary", False]];
    grading = If[antiunitary, -1, 1];
    linear = Lookup[reciprocal, "LinearPart", grading IdentityMatrix[3]];
    shift = Lookup[reciprocal, "FractionalTranslation", {0, 0, 0}];
    eta = Lookup[detail, "eta_g", None];
    If[!MemberQ[{-1, 1}, eta], eta = If[axisDefined, 1, notApplicableEta[]]];
    <|
      "Name" -> internalName,
      "InternalName" -> internalName,
      "RealSpaceSeitz" -> {IdentityMatrix[3], UnitVector[3, index]},
      "ReciprocalSpaceSeitz" -> {exactDisplayValue[linear], exactDisplayValue[shift]},
      "HasFractionalShift" -> AnyTrue[Flatten[exactDisplayValue[shift]], # =!= 0 &],
      "Antiunitary" -> antiunitary,
      "Grading" -> grading,
      "Eta" -> eta
    |>
  ];

  makePointOrSpin[internalName_String] := Module[
    {reciprocal, detail, matrix, translation, name, eta},
    reciprocal = Lookup[reciprocalByName, internalName];
    detail = Lookup[derivationByName, internalName, <||>];
    matrix = exactDisplayValue[Lookup[detail, "M_parent", IdentityMatrix[3]]];
    translation = exactDisplayValue[
      Lookup[detail, "seitz_translation", {{0}, {0}, {0}}]
    ];
    name = Which[
      internalName === "zeta_coplanar", "zeta",
      StringStartsQ[internalName, "g"], rotationNameFromMatrix[parent, matrix],
      True, internalName
    ];
    eta = Lookup[detail, "eta_g", None];
    If[eta === None && internalName === "zeta_coplanar", eta = 1];
    If[!MemberQ[{-1, 1}, eta], eta = notApplicableEta[]];
    <|
      "Name" -> name,
      "InternalName" -> internalName,
      "RealSpaceSeitz" -> {matrix, Flatten[translation]},
      "ReciprocalSpaceSeitz" -> exactDisplayValue[Lookup[reciprocal, "Seitz"]],
      "HasFractionalShift" -> nonzeroShiftQ[reciprocal],
      "Antiunitary" -> TrueQ[Lookup[reciprocal, "Antiunitary"]],
      "Grading" -> Lookup[reciprocal, "Grading"],
      "Eta" -> eta
    |>
  ];

  translations = makeTranslation /@ Range[3];
  pointAndSpinNames = Select[Lookup[reciprocalGenerators, "Name", {}],
    StringStartsQ[#, "g"] || # === "zeta_coplanar" &];
  pointAndSpinGenerators = makePointOrSpin /@ pointAndSpinNames;
  generators = Join[translations, pointAndSpinGenerators];
  <|
    "SSGNumber" -> ssg,
    "ParentSpaceGroup" -> parent,
    "ParentSpaceGroupSymbol" -> "",
    "ParentBravaisLattice" -> Lookup[$rotationNameData["SpaceGroupBravais"], ToString[parent]],
    "LB" -> lb,
    "ReciprocalBasisMatrix" -> reciprocalBasis,
    "BZVolumeRatioToParent" -> 1/latticeIndex,
    "Nonsymmorphic" -> TrueQ[Lookup[record, "Nonsymmorphic", False]],
    "Generators" -> generators
  |>
];
getSSGReciprocalGenTab[ssg_] := Missing["InvalidSSGNumber", ssg];

etaTableValue[value_] := If[MissingQ[value], "-", value];

showSSGReciprocalGenTab[ssg_String] := Module[
  {data, generators, headers, table, styleMajor, styleMinor, globalLabel,
   realSeitz, reciprocalSeitz},
  data = getSSGReciprocalGenTab[ssg];
  If[MissingQ[data], Return[data]];
  generators = data["Generators"];
  headers = Style[#, Bold] & /@ Lookup[generators, "Name"];
  realSeitz = seitzDisplay @@@ Lookup[generators, "RealSpaceSeitz"];
  reciprocalSeitz = seitzDisplay @@@ Lookup[generators, "ReciprocalSpaceSeitz"];
  styleMajor = Directive[Black, Thickness[2]];
  styleMinor = Directive[Thin, GrayLevel[0.8]];
  table = Grid[
    {
      Prepend[headers, Style["Generator", Bold]],
      Prepend[realSeitz, Style["Real {M|t}", Bold]],
      Prepend[reciprocalSeitz, Style["Recip. {A|Q}", Bold]],
      Prepend[If[TrueQ[#], "Yes", "No"] & /@ Lookup[generators, "HasFractionalShift"],
        Style["Nonzero Q", Bold]],
      Prepend[If[TrueQ[#], "Yes", "No"] & /@ Lookup[generators, "Antiunitary"],
        Style["Antiunitary", Bold]],
      Prepend[etaTableValue /@ Lookup[generators, "Eta"], Style["eta_g", Bold]]
    },
    Frame -> All, Alignment -> Center, ItemSize -> Full,
    Dividers -> {
      {{{styleMinor}}, {1 -> styleMajor, 2 -> styleMajor, -1 -> styleMajor}},
      {{{styleMinor}}, {1 -> styleMajor, 2 -> styleMajor, 4 -> styleMajor, -1 -> styleMajor}}
    },
    Background -> {None, None, {
      {{1, 1}, {1, -1}} -> Lighter[Yellow, 0.88],
      {{2, 3}, {1, -1}} -> Lighter[Green, 0.95]
    }},
    Spacings -> {1.1, 0.75}
  ];
  globalLabel = If[data["Nonsymmorphic"], "Yes", "No"];
  Column[{
    Row[{"SSG ", Style[data["SSGNumber"], Bold], "   Parent SG No. ",
      data["ParentSpaceGroup"], " ", data["ParentSpaceGroupSymbol"]}],
    Row[{Subscript[Style["L", Italic], "B"], " = ", MatrixForm[data["LB"]],
      "    reciprocal basis = ", MatrixForm[data["ReciprocalBasisMatrix"]]}],
    Row[{"BZ coordinate cell: parallelepiped spanned by the columns of ",
      Superscript[Subscript[Style["L", Italic], "B"], "-T"],
      "; volume ratio to the parent BZ = ", data["BZVolumeRatioToParent"], "."}],
    Row[{"Momentum-space nonsymmorphic: ", Style[globalLabel, Bold]}],
    Pane[table, ImageSize -> Full, Scrollbars -> {True, False}],
    Style[
      "Real-space Seitz data use the parent primitive-lattice coordinates. Reciprocal Seitz data use the BZ basis defined by L_B. 'Nonzero Q' refers to the stored momentum-origin convention; intrinsic nonsymmorphicity is the global common-origin result shown above. eta_g is defined only when the translation image selects a unique common spin axis.",
      Smaller, GrayLevel[0.3]
    ]
  }, Spacings -> 1.0]
];
showSSGReciprocalGenTab[ssg_] := Missing["InvalidSSGNumber", ssg];

SSGReciprocalSymmetryTable[ssg_] := showSSGReciprocalGenTab[ssg];

End[];
EndPackage[];
