(* Bootstrap installer for SSGReciprocalDatabase 0.8.2. *)
Module[
  {version = "0.8.2", pacletBase, requiredDirectories, localAsset,
   releaseURL, source, installed},

  Needs["PacletManager`"];
  pacletBase = If[
    StringQ[PacletManager`$UserBasePacletsDirectory],
    PacletManager`$UserBasePacletsDirectory,
    FileNameJoin[{$UserBaseDirectory, "Paclets"}]
  ];
  requiredDirectories =
    FileNameJoin[{pacletBase, #}] & /@
      {"Repository", "Temporary", "Configuration", "Cached"};
  Scan[
    If[!DirectoryQ[#],
      CreateDirectory[#, CreateIntermediateDirectories -> True]
    ] &,
    requiredDirectories
  ];

  localAsset = If[StringQ[$InputFileName] && FileExistsQ[$InputFileName],
    FileNameJoin[{DirectoryName[$InputFileName],
      "SSGReciprocalDatabase-" <> version <> ".paclet"}],
    ""
  ];
  releaseURL =
    "https://github.com/Peiyuan-Wang/SSGReciprocalDatabase/releases/download/v" <>
      version <> "/SSGReciprocalDatabase-" <> version <> ".paclet";
  source = Which[
    ValueQ[$SSGReciprocalDatabasePacletSource] &&
      StringQ[$SSGReciprocalDatabasePacletSource],
        $SSGReciprocalDatabasePacletSource,
    FileExistsQ[localAsset], localAsset,
    True, releaseURL
  ];

  installed = PacletInstall[source, ForceVersionInstall -> True];
  If[Head[installed] =!= PacletObject,
    Print["SSGReciprocalDatabase installation failed from: ", source];
    Return[$Failed]
  ];
  Get["SSGReciprocalDatabase`"];
  Print["SSGReciprocalDatabase ", version, " installed and loaded from ",
    installed["Location"], "."];
  installed
]
