# Requirements

## Summary

Levels follow PCBA to USD Input Contract **1.0.2**.

- The board asset **MUST** have a single `defaultPrim` (name free) and a board-root prim
  discoverable by its `pcba:board:*` metadata — provenance, packaging manifest, thickness,
  origin convention. The root may be the default prim, a child of a wrapper, or a panel's
  class master; `pcba:board:name` is board-root only (UO.001).
- A `board_substrate` mesh **MUST** exist. The side-grouped hierarchy the contract illustrates
  (layers, components, copper, paste, holes, registries) is desirable, not required; discovery
  is by `pcba:mesh:role` and `pcba:*` attributes, never by prim name (UO.003).
- Stage conventions are **MUST**: `metersPerUnit = 0.001`, `upAxis = Z`, no compensating root
  scale/rotation, board in the XY plane with Z as the normal (UO.006).
- A `Registries` scope **SHOULD** expose `rel pcba:board:members` listing **every** placed
  component, all mount classes. It is an index, not a source of truth (UO.008).
- Every `Mesh` **MUST** carry an authoritative `pcba:mesh:role` token from the contract
  vocabulary; prim names must not replace it; no solder roles (UO.009).
- All contract attributes **MUST** live under `pcba:` in the recognized scopes
  (`component`, `mesh`, `pin`, `board`, `prov`, `layer`, `panel`, `fixture`, `variance`);
  unknown scopes are advisory warnings (UO.010).
- Renderable meshes **SHOULD** bind a material of the role's class; `pcba:mesh:matClass` is
  explicit on `pkg_*` / `fixture_*` and derived on `board_*` (UO.011).
- References/payloads **MUST** be relative and self-contained; the board is one asset placed
  per panel position; repeated parts reference one prototype with `instanceable = true`
  (UO.012).
- A distributed package **MUST** author `pcba:board:packageManifest` inventorying the packaged
  files, distinct from the CI.007 component manifest (UO.013).
- The board root **MUST** declare `pcba:board:originConvention`; `originPointMm` **MUST**
  accompany `datum_explicit` (UO.014).
- The board root **MUST** carry `pcba:board:generatorVersion` and `pcba:board:contentHash`
  (UO.015).
- Asset file names **SHOULD** be clean ASCII with no spaces or parentheses (UO.016).
- Where a mesh role determines its material class, the bound material **MUST** agree with it,
  checked by class (UO.017).

## Requirements

```{requirements-table}
```

```{toctree}
:maxdepth: 1
:hidden:

requirements/board-root
requirements/stage-layout
requirements/stage-conventions
requirements/registries
requirements/mesh-role
requirements/namespace
requirements/material-binding
requirements/packaging-relative
requirements/package-manifest
requirements/origin-convention
requirements/provenance
requirements/file-naming
requirements/role-material
```
