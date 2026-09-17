# SSGReciprocalDatabase 0.8.3

This release adds standard operation names to the reciprocal magnetic-group
correspondence table.

- `showSSGReciprocalMagneticGroup[ssg]` now includes a `Parent operation`
  column and an `MSG operation` column.
- Parent names are recovered exactly from the graded momentum action
  `A_g = s_g M_g^(-T)` and the embedded Bloch lattice.
- MSG names are evaluated in the standard magnetic-group coordinates;
  antiunitary operation names carry a prime.
- Names use the bundled, validated `SpaceGroupIrep` rotation-name tables.
- The underlying 67,475-record database is unchanged.
