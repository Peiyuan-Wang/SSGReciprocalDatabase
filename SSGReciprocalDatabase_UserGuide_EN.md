# SSGReciprocalDatabase 0.6.0 User Guide

## 1. Overview

`SSGReciprocalDatabase` is a Wolfram Language package for reciprocal-space
symmetry data of the 67,475 spin space groups (SSGs) classified by Xiao et
al. An SSG is addressed by its Xiao label, for example `"N143.10.1"`.

For each SSG the package provides the physical Bloch lattice, real-space and
reciprocal-space generators, unitary grading, momentum-space fractional
translations, the closed reciprocal action group, and the global
momentum-origin test for nonsymmorphicity.

The package uses official ISO-IR Miller--Love/CDML representation data. Spatial
operations are stored in primitive direct-lattice coordinates. If

```text
f_g(k) = A_g k + Q_g,
```

then

```text
A_g = s_g M_g^(-T),
```

where `M_g` is the spatial integer matrix and `s_g` is `+1` for a unitary
operation and `-1` for an antiunitary operation.

## 2. Installation and loading

Place the directory `SSGReciprocalDatabase` in one of the Wolfram application
directories, such as:

```text
$UserBaseDirectory/Applications/
```

Load or explicitly reload the package with:

```wl
<< "SSGReciprocalDatabase`"
```

The package follows the reload convention used by `SpaceGroupIrep`: every
explicit `Get` first clears its old public and private definitions and then
redefines them. `Needs` may instead be used for a one-time load:

```wl
Needs["SSGReciprocalDatabase`"]
```

`Needs` does not reload an already loaded package. During development, use
`<< "SSGReciprocalDatabase`"` after changing the package on disk.

Generator labels such as `C3+`, `C2z`, and `sigma_x` come from a bundled
snapshot of the `SpaceGroupIrep` rotation-name tables. The database therefore
uses the same Jones-symbol naming source without loading `SpaceGroupIrep` at
run time.

## 3. Database coverage and labels

### `SSGReciprocalDatabaseVersion`

Returns the package version.

```wl
SSGReciprocalDatabaseVersion
```

### `SSGReciprocalDatabaseStatus[]`

Returns database coverage, source convention, schema version, and validation
metadata.

```wl
SSGReciprocalDatabaseStatus[]
```

### `SSGReciprocalDatabaseLabels[]`

Returns all indexed Xiao SSG labels.

```wl
labels = SSGReciprocalDatabaseLabels[];
Length[labels]
```

The expected length is `67475`.

## 4. Complete record lookup

### `getSSGReciprocalData[ssg]`

Returns the complete stored association for an SSG.

```wl
data = getSSGReciprocalData["N143.10.1"];
Keys[data]
```

The record includes `LB`, `ReciprocalGenerators`, `GeneratorDerivation`,
`OriginTest`, `GradedReciprocalGroupElements`, and provenance fields.

### `getSSGNonsymmorphic[ssg]`

Returns `True` when no single momentum-origin shift removes all stored
fractional translations, and `False` otherwise.

```wl
getSSGNonsymmorphic["N6.9.19"]
```

### `getSSGNonsymmorphicInfo[ssg]`

Returns the nonsymmorphic result together with its evidence source.

```wl
getSSGNonsymmorphicInfo["N6.9.19"]
```

### `getSSGLB[ssg]`

Returns the column-Hermite-normal-form basis matrix of the physical Bloch
lattice `L_B`, expressed in the parent primitive direct-lattice basis.

```wl
getSSGLB["N143.10.1"]
```

The reciprocal basis associated with this Bloch lattice is `Inverse[LB]^T`.

## 5. Generator data and formatted tables

### `getSSGReciprocalGenTab[ssg]`

Returns a compact association designed for further computation. It always
contains the three parent primitive translations `T1`, `T2`, and `T3`, followed
by the selected spatial point generators and, for coplanar SSGs, the additional
pure-spin generator `zeta`.

```wl
genData = getSSGReciprocalGenTab["N143.10.1"];
genData["Generators"]
```

Each generator contains:

- `Name`: crystallographic rotation name used in the displayed table;
- `InternalName`: stable database identifier;
- `RealSpaceSeitz`: `{M_g,t_g}` in parent primitive coordinates;
- `ReciprocalSpaceSeitz`: `{A_g,Q_g}` in the `L_B` reciprocal basis;
- `HasFractionalShift`: whether the stored representative has `Q_g != 0`;
- `Antiunitary` and `Grading`;
- `Eta`: the common-spin-axis sign, or `Missing["NotApplicable",...]`.

### `showSSGReciprocalGenTab[ssg]`

Displays an English table modeled on the table style of `SpaceGroupIrep`.

```wl
showSSGReciprocalGenTab["N143.10.1"]
```

The table rows are `Real {M|t}`, `Recip. {A|Q}`, `Nonzero Q`, `Antiunitary`,
and `eta_g`. A dash is displayed when `eta_g` is not defined. The text above
the table reports `L_B`, its reciprocal basis, the relative BZ volume, and the
global momentum-space nonsymmorphic result.

`Nonzero Q` is a statement about the stored momentum-origin convention. The
global nonsymmorphic result is stronger: it tests whether one common origin
shift can remove all `Q_g` simultaneously.

### `SSGReciprocalSymmetryTable[ssg]`

Compatibility alias for `showSSGReciprocalGenTab[ssg]`.

## 6. Reciprocal group elements

### `SSGReciprocalGenElem[ssg]`

Returns the reciprocal generators used in the affine group calculation. The
three ordinary lattice translations are not repeated here when they act
trivially on momentum; use `getSSGReciprocalGenTab` for the complete displayed
generator set.

### `SSGReciprocalGroupElements[ssg]`

Returns the closed momentum-action group as Seitz pairs `(A_g,Q_g)`, with the
unitary grading forgotten.

### `SSGGradedReciprocalGroupElements[ssg]`

Returns the closed reciprocal group while retaining the unitary/antiunitary
grading.

```wl
SSGReciprocalGenElem["N6.9.19"]
SSGReciprocalGroupElements["N6.9.19"]
SSGGradedReciprocalGroupElements["N6.9.19"]
```

## 7. O(3) representation data

### `getSSGO3RepresentationData[ssg]`

Returns the Xiao-to-ISO-IR representation record.

### `getSSGO3RepresentationAlternatives[ssg]`

Returns all official ISO-IR representatives associated with the Xiao class.

### `SSGO3SeitzOperators[ssg, Alternative -> n]`

Returns the official ISO-IR representative Seitz operators. Alternatives are
numbered from one in the Wolfram Language interface.

### `SSGO3RepresentationMatrices[ssg, opts]`

Returns the exact O(1), O(2), or O(3) representation matrices.

### `SSGO3EmbeddedRepresentationMatrices[ssg, opts]`

Embeds O(1) and O(2) matrices into a uniform O(3) form.

### `SSGO3RepresentationDatabaseStatus[]`

Returns the O(3) source and validation metadata.

Example:

```wl
SSGO3RepresentationMatrices[
  "P143.5.1",
  Alternative -> 1,
  Parameters -> {{0, 0, u}}
]
```

## 8. On-demand recomputation

### `SSGRecomputeReciprocalData[ssg, opts]`

Recomputes one reciprocal record from the installed ISO-IR-backed source and
caches the result under `$UserBaseDirectory/ApplicationData`.

```wl
SSGRecomputeReciprocalData["N6.9.19"]
```

Options:

- `Alternative -> n` selects an ISO-IR representative;
- `Parameters -> Automatic` uses the generic parameter convention;
- `Parameters -> {{alpha,beta,gamma},...}` evaluates an explicit parameter
  point for each direct-sum constituent.

## 9. Troubleshooting

If a public symbol appears in both `Global`` and `SSGReciprocalDatabase``:

```wl
Remove["Global`getSSG*"];
Remove["Global`showSSG*"];
Remove["Global`SSG*"];
<< "SSGReciprocalDatabase`"
```

Do not place a first-time package load and an unqualified package function in
the same input cell. Load the package in one cell and call functions in the
next cell, or use the fully qualified name.

To check which file was loaded:

```wl
FindFile["SSGReciprocalDatabase`"]
```

The package data have passed exhaustive mechanical checks, but those checks do
not replace independent scientific review of the underlying physical claims.
