# SSGReciprocalDatabase 0.8.4

This release makes the reciprocal magnetic-group display a generator table for
the full space group rather than a list of point-operation projections.

- `showSSGReciprocalMagneticGroup[ssg]` now starts with all three
  reciprocal-lattice translation generators and then lists every stored SSG
  quotient generator.
- The source and standard linear/translation data are merged into complete
  Seitz columns named `Momentum space symmetry of SSG` and
  `Real space symmetry of MSG`.
- Source reciprocal translations are transformed exactly by the same
  coordinate certificate used for the quotient generators.
- SSG and MSG generator names are shown separately; antiunitary MSG names carry
  a prime.
- Tests cover the complete generator list and its exact source-to-standard
  correspondence for `N143.10.1`.
- The underlying 67,475-record reciprocal database is unchanged.
