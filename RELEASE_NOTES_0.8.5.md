# SSGReciprocalDatabase 0.8.5

This patch clarifies the meaning of the standardized magnetic-group column in
`showSSGReciprocalMagneticGroup[ssg]`.

- The column previously titled `Real space symmetry of MSG` is now titled
  `Corresponding standard MSG Seitz operation`.
- The new name states that the output is an affine Seitz correspondence with a
  standard magnetic space group acting on an abstract three-dimensional
  Euclidean space. It does not identify the column with the conventional
  reciprocal action of a real-space MSG on Bloch momentum.
- The underlying coordinate transformation, generator data, magnetic-group
  identifications, and 67,475 database records are unchanged.
