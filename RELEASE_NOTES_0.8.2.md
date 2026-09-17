# SSGReciprocalDatabase 0.8.2

This release adds a first-install bootstrap for Wolfram systems where
`$UserBaseDirectory/Paclets/Repository` has not yet been created.

- `InstallSSGReciprocalDatabase.wl` creates the standard user paclet
  directories before invoking `PacletInstall`.
- A new user can install and load the package with one `Get[...]` command.
- Local `.paclet` installation instructions now include repository
  initialization.
- The database content and all 24 public query functions are unchanged from
  version 0.8.1.
