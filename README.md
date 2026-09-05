# SSG reciprocal-group enumerator

This directory contains an exact enumerator for reciprocal affine actions of
spin-space groups (SSGs).  It uses lattice coordinates throughout.

For every generator the input must provide

- the direct-lattice integer matrix `M`;
- the unitary grading `s` (`+1` unitary, `-1` antiunitary);
- the reciprocal shift `Q` in the physical Bloch-lattice basis.

For common-axis records, `kappa` may be supplied instead of `Q`; the parser
then uses `Q=kappa/2` componentwise.

The induced action is

```text
k -> A_g k + Q_g,       A_g = s_g M_g^(-T),       k in R^d/Z^d.
```

The program performs the following exact calculations:

1. closes the affine group modulo reciprocal lattice vectors;
2. compares its affine and linear orders;
3. solves the common-origin equations `(I-A_g) theta = Q_g (mod Z)` by a
   Smith decomposition with unimodular transformations;
4. marks a shift as intrinsic only when the common system is inconsistent;
5. tests fixed points for every nonidentity element and for the whole group;
6. classifies the generator data `(A_g,Q_g)` after quotienting common
   `U(1)` origin shifts and internal `GL(3,Z)` changes of the Bloch-lattice
   basis.

## Run the verified example

```bash
cd /Users/wpy/Desktop/ai4s/shangjiao/theory-paper-codex-harness/try/computations/ssg_reciprocal_catalog
python3 -m unittest -v
python3 enumerate_reciprocal_groups.py example_records.json -o example_catalog.json
```

The `N6.9.19` witness is intrinsic and fixed-point-free; the control example
has a half shift in the mirror-reversed direction and is origin-removable.

## Extract the Xiao table candidates

```bash
python3 extract_xiao_candidates.py \
  --pdf "/Users/wpy/Desktop/ai4s/shangjiao/theory-paper-codex-harness/try/papers/backgroud/Xiao 等 - 2024 - Spin Space Groups Full Classification and Applica.pdf" \
  -o xiao_nonsymmorphic_candidates.json
```

Appendix F and `O3_Rep_Class` do not by themselves contain the generator
matrices or spin lifts needed to reconstruct every `Q_g`.  The standalone
candidate extractor therefore remains fail-closed.  The parent-group command
described below resolves supported labels through `SpaceGroupIrep`.

To inventory every representation class in the supplied official archive:

```bash
python3 inventory_o3_rep_class.py \
  ../xiao_o3_rep_class/AllO3_Rep \
  --xiao-candidates xiao_nonsymmorphic_candidates.json \
  -o all_o3_classes_blocked.json
python3 enumerate_reciprocal_groups.py \
  all_o3_classes_blocked.json -o all_o3_catalog_status.json
```

## Complete Xiao O(3) representation source

The file official_sources/iso_ir/XiaoO3RepresentationSource.json resolves
every one of the 67,475 Xiao L/P/N labels to official ISO-IR physically
irreducible representation matrices. It uses Miller-Love/CDML labels and
ISO-IR representative Seitz operators throughout, so no BC/BCS label-order
inference is involved.

A Xiao label can denote several equivalent PIR representatives. The data
source preserves all of them under Alternatives; alternative 1 is a
deterministic representative, not a claim that the equivalence class has only
one matrix realization. Parameterized k labels retain exact alpha, beta,
gamma dependence using the official ISO-IR reconstruction formula.

The O(3) representation source and the derived reciprocal database are both
complete for all 67,475 Xiao labels.  The latter is split into 230 parent-space-
group shards, so a Mathematica query loads only the requested parent group.
Every stored record has status `COMPLETE`; the exhaustive validator finds no
disagreement with the Xiao symmorphic/nonsymmorphic labels.

## Recompute one SSG from the official source

The package version 0.4.0 also retains an on-demand exact path. In Mathematica:

```wl
Needs["SSGReciprocalDatabase`"]
SSGRecomputeReciprocalData["N6.9.19"]
getSSGLB["N6.9.19"]
SSGReciprocalGenElem["N6.9.19"]
SSGReciprocalGroupElements["N6.9.19"]
```

The recomputation uses ISO-IR Miller-Love/CDML labels and representative
Seitz operators. Spatial matrices are converted from the ISO-IR conventional
setting to the primitive direct-lattice basis `B` by `M=B^-1 R B`; `L_B` is
stored in that primitive basis. The momentum action is
`k -> s M^(-T) k + Q`. Results are cached below the Wolfram user application
data directory and take precedence over legacy database entries.

For a parameterized PIR family the default is the exact generic representative
`(11/100,3/25,13/100)`, matching the arbitrary non-special-k values used by
the official ISO-IR sample program. The derived discrete data are constant on
each connected generic parameter stratum. To inspect a special parameter value,
pass one triple per direct-sum constituent:

```wl
SSGRecomputeReciprocalData[
  "P1.5.1", Parameters -> {{"1/2", "0", "0"}}
]
```

At a high-symmetry endpoint or intersection the representation can reduce or
move to another Xiao class. Such an explicit evaluation is retained, but it
must be compared with the corresponding special-k label before being treated
as a distinct SSG result.

## Completeness and representative convention

The packaged catalog contains all 67,475 Xiao SSG labels and has no
`Missing` or `Unsupported` reciprocal records. `enumerate_parent_sg.py`
derives the data from the complete ISO-IR-backed O(3) source rather than from
BC/BCS label matching. For a Xiao class with several equivalent ISO-IR PIR
realizations, the catalog uses alternative 1 as a deterministic canonical
representative; all alternatives remain available through the O(3) interface.

For a parameterized PIR family the packaged record uses the exact generic
sample `(11/100,3/25,13/100)`. Special endpoints or intersections are separate
representation strata and should be queried through their corresponding Xiao
labels or evaluated explicitly with `SSGRecomputeReciprocalData`.

The embedded Bloch sublattice is retained as physical data.  Its basis is
stored in canonical column HNF, so replacing a basis matrix `B` by `B U` with
`U in GL(3,Z)` does not create a new class.  Distinct embedded sublattices,
including equal-index expansions in different parent-lattice directions, are
not identified.

## One-command pipeline

```bash
python3 run_catalog_pipeline.py \
  --xiao-pdf "/Users/wpy/Desktop/ai4s/shangjiao/theory-paper-codex-harness/try/papers/backgroud/Xiao 等 - 2024 - Spin Space Groups Full Classification and Applica.pdf" \
  --o3-archive ../xiao_o3_rep_class/AllO3_Rep \
  --output-dir run
```

The pipeline writes `RUN_STATUS.md`, preserves the blocked inventory, and
separately catalogs every generator-complete record.

## Enumerate one parent space group from Xiao labels

`enumerate_parent_sg.py` combines the Appendix-F representative labels with
exact generator matrices exported from the installed `SpaceGroupIrep`
package.  For example,

```bash
python3 enumerate_parent_sg.py 6 --order N \
  -o sg6_noncoplanar_reciprocal_groups.json
```

The command also writes `sg6_noncoplanar_reciprocal_groups.md`.  Use
`--markdown PATH` to choose another summary path.  The JSON contains detailed
per-SSG derivations and a `reciprocal_symmetry_classes` array that groups the
generator data under the equivalence relation below and lists every
corresponding Xiao label.

The program performs the following steps for each row of the selected parent
space group:

1. reconstructs the listed real `O(2)` or `O(3)` representation;
2. uses `det rho(g)` to determine the unitary grading;
3. constructs the maximal unitary translation lattice `T_U` and rewrites the
   parent point matrices in its primitive basis;
4. computes the `Pin^-(3)` lift signs, `eta_g`, `kappa_g`, and
   `Q_g=kappa_g/2`;
5. includes antiunitary parent translations as coset representatives of the
   full graded SSG;
6. applies the common-origin Smith test and closes the reciprocal affine group.

The final classification uses the following equivalence relation:

1. the embedded unitary Bloch sublattice must have the same HNF matrix in the
   standard parent-lattice basis; equal indices with different expansion
   directions are not identified;
2. the generator multisets `(s_g,A_g)` must agree, allowing permutations among
   repeated identical linear actions;
3. two shift assignments are identified exactly when one common
   `theta in Hom(L_B,U(1))` relates them by
   `Q'_g=Q_g-(I-A_g)theta`;
4. basis changes inside a fixed `L_B` are removed by recanonicalizing its basis
   to HNF, which is invariant under right multiplication by `GL(3,Z)`; distinct
   embedded HNF sublattices remain distinct by design.

Each class reports a representative with the smallest possible number of
nonzero generator shifts.  A removable class is therefore displayed with all
`Q_g=0`.  This classifies the generator-level `(A_g,[Q_g])` data and no longer
uses the raw affine-group hash as the equivalence criterion.

The public Markdown classification table contains only `L_B`, the generator
actions `(s_g,A_g)`, and a representative of `[Q]`.  It omits affine order,
linear order, and the derived intrinsic flag.  Every class occupies two rows:
the column-HNF representative and an explicitly transformed coordinate form
with `B'=B U`, `k'=U^T k`, `A'_g=U^T A_g U^{-T}`, and `Q'_g=U^T Q_g`.

The program then closes each `(A_g,Q_g)` action as a three-dimensional
crystallographic group and identifies its ordinary international space-group
type with `spglib`.  This is a second, coarser quotient: distinct
SSG-resolved `(L_B,A_g,[Q])` classes may define the same ordinary reciprocal
space group because the latter forgets the SSG grading, parent-lattice
embedding, spin representation, and generator presentation.  The JSON field
`reciprocal_space_group_classes` contains one entry per distinct international
space-group number and lists all finer SSG-resolved realizations below it.

For parent SG 6, the 41 SSG-resolved classes reduce to 10 distinct ordinary
reciprocal space groups: Nos. 3, 4, 6, 7, and 10--15.

## Mathematica SSG database

The installed `SSGReciprocalDatabase`` package is indexed by the Xiao SSG
number. In Mathematica use

```wolfram
<< "SSGReciprocalDatabase`"
getSSGNonsymmorphic["N6.9.19"]
getSSGNonsymmorphicInfo["N6.9.19"]
getSSGLB["P6.3.7"]
SSGReciprocalGenElem["P6.3.7"]
getSSGReciprocalData["P6.3.7"]
SSGReciprocalGroupElements["N6.9.19"]
SSGGradedReciprocalGroupElements["N6.9.19"]
getSSGReciprocalGenTab["N143.10.1"]
showSSGReciprocalGenTab["N143.10.1"]
Length[SSGReciprocalDatabaseLabels[]]
SSGReciprocalDatabaseStatus[]
```

An explicit `Get` (`<<`) clears and reloads the package definitions, following
the convention used by `SpaceGroupIrep`. `Needs` remains available for a
one-time load. The displayed generator table always includes `T1`, `T2`, and
`T3`, followed by all selected point generators, and uses a bundled snapshot
of the crystallographic operation names in the `SpaceGroupIrep` Jones-symbol
tables.

`getSSGLB` returns a column-HNF basis for the center of the unitary
translation-lift group. This includes the radical reduction for noncommuting
translation projectivity. Every reciprocal generator reports the direct-space
integer matrix `SpatialPointMatrix=M_g`, grading `Grading=s_g`, momentum matrix
`MomentumLinearPart=LinearPart=s_g M_g^(-T)`, shift
`FractionalTranslation=Q_g`, and the momentum-space `Seitz={A_g,Q_g}` pair.
`SSGReciprocalGroupElements` forgets the grading after forming the momentum
action, while `SSGGradedReciprocalGroupElements` retains it.

The complete English reference is provided in
`SSGReciprocalDatabase_UserGuide_EN.md` and
`SSGReciprocalDatabase_UserGuide_EN.docx`.

The database contains 67,475 complete records across all 230 parent space
groups: 18,801 are nonsymmorphic and 48,674 are symmorphic under the stored
common-origin test. The full validator checks the exact label set, status,
Xiao-flag agreement, `M_g^T A_g=s_g I`, half-quantization of `Q_g`, invariance
of `L_B`, graded closure, and the forgetful map to the momentum-action group.
These are mechanical and algebraic checks of the implemented convention; they
do not replace independent scientific review of the underlying classification.

## Complete O(3) Mathematica interface

The same package now exposes the complete Xiao-to-ISO-IR representation
source. Mathematica alternatives are one-based. Parameters contains one
{alpha,beta,gamma} triple per PIR constituent; Automatic returns symbolic
parameters.

    getSSGO3RepresentationData["N143.11.1"]
    getSSGO3RepresentationAlternatives["N143.11.1"]
    SSGO3SeitzOperators["P143.5.1", Alternative -> 1]
    SSGO3RepresentationMatrices[
      "P143.5.1",
      Alternative -> 1,
      Parameters -> {{0, 0, u}}
    ]
    SSGO3EmbeddedRepresentationMatrices["P143.5.1"]
    SSGO3RepresentationDatabaseStatus[]

The Seitz and matrix lists contain the three primitive translation generators
first, followed by one official ISO-IR representative for each point
operation. Data are split into 230 parent-SG shards, so each query loads only
the requested space group.

## Bilbao REPRES source cache

New BCS-convention representation data must be acquired from the official
Bilbao REPRES service rather than inferred from the ordering of BC-convention
Mathematica records.  Download one k-vector record with

```bash
python3 bilbao_repres_source.py fetch 75 Z 0 0 1/2 --basis p --endpoint text
```

The command stores the raw response, SHA-256 hash, exact query, retrieval time,
BCS convention statement, and a parsed status under `bilbao_repres_cache/`.
The raw cache is append-safe unless `--force` is supplied.  Empty replies,
server errors, unrecognized documents, and Cloudflare challenges are retained
as `BLOCKED_*` provenance records and are never imported into
`parent_irrep_cache`.

Rebuild the compact index after moving or auditing record files with
`python3 bilbao_repres_source.py reindex`.

If REPRES requires an interactive browser verification, save the unmodified
result page and import it without changing its scientific content:

```bash
python3 bilbao_repres_source.py import-response 75 Z 0 0 1/2 \
  --basis p --endpoint text /absolute/path/to/repres-response.txt
```

The current `representations_out.pl` HTML output is also supported.  For a
browser-saved result use `--endpoint html`; the parser extracts the parent SG,
parameterized k-vector, Seitz generators, BCS labels, and symbolic matrices.

The legacy `parent_irrep_cache` remains development-only until every label is
reconstructed from a verified Bilbao response and cross-checked against the
official Xiao `O3_Rep_Class` representative.  A matching k-vector name alone
is not sufficient: the BCS label, setting, coordinates, generator order, and
matrix block must all agree.
