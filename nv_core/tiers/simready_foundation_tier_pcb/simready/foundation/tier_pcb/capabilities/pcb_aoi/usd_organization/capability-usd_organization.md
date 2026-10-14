# PCB USD Organization

## Overview

This capability defines **how a PCB board USD is organized so a downstream pipeline can
discover its geometry and metadata by role and attribute** rather than by prim name or
hierarchy position. It realizes the *USD Organization (UO)* codes of the PCBA to USD Input
Contract **1.0.2** (section 2 conventions, 3 stage layout, 4 composition and packaging, 9 mesh
roles, 11 board root, 14 not-yet-available fields, and the `pcba:` namespace rules of section 1).

The board USD is arranged around a small set of stable conventions:

- **Stage conventions** — `metersPerUnit = 0.001`, `upAxis = "Z"`, board in the XY plane with
  +Z as the normal, no compensating root transform, a single `defaultPrim` whose name is free.
- **Board root** — the prim carrying the `pcba:board:*` metadata (provenance, packaging,
  thickness, origin convention). It is discovered by those attributes; it may be the default
  prim, a child of a scene wrapper, or a panel's class master.
- **Stage layout** — a desirable, not mandatory, hierarchy: substrate, side-grouped layers with
  components / copper / paste, holes, registries. The only MUST is a `board_substrate` mesh.
- **Mesh-role discovery** — every `Mesh` carries an authoritative `pcba:mesh:role` token.
- **Namespace** — every contract attribute lives under `pcba:`, in nine recognized scopes;
  authored as ordinary custom attributes, no schema required.
- **Component registry** — a `pcba:board:members` index of every placed component (SHOULD; an
  index, not a source of truth).
- **Packaging** — relative, self-contained references; one board asset placed per panel
  position; repeated parts instanced from a shared prototype.
- **Provenance and manifest** — generator version, content hash, and a package-file manifest on
  the board root.

## Not-yet-available fields

A MUST field whose upstream data is not available yet MAY be omitted, provided the prim that
would carry it authors `pcba:prov:<leaf> = "not_yet_available"` (or `"source_data_required"`
where sourcing was attempted and failed). `<leaf>` is the bare leaf name. Validators report the
marker as a **declared gap**, not a failure, so partial exports can be validated and tracked.

## Requirements

| Code | Requirement | Summary |
|------|-------------|---------|
| UO.001 | [board-root](/capabilities/pcb_aoi/usd_organization/requirements/board-root) | Single `defaultPrim` (name free); a board-root prim discoverable by its `pcba:board:*` metadata; `pcba:board:name` board-root only. |
| UO.003 | [stage-layout](/capabilities/pcb_aoi/usd_organization/requirements/stage-layout) | A `board_substrate` mesh MUST exist; the illustrated hierarchy is desirable, not required; discovery by role and attribute. |
| UO.006 | [stage-conventions](/capabilities/pcb_aoi/usd_organization/requirements/stage-conventions) | `metersPerUnit = 0.001`, `upAxis = Z`, no compensating root transform; board in XY, Z normal. |
| UO.008 | [registries](/capabilities/pcb_aoi/usd_organization/requirements/registries) | SHOULD: `rel pcba:board:members` → every placed component, all mount classes; an index, not identity authority. |
| UO.009 | [mesh-role](/capabilities/pcb_aoi/usd_organization/requirements/mesh-role) | Authoritative `pcba:mesh:role` token on every `Mesh` from the contract vocabulary; no solder roles. |
| UO.010 | [namespace](/capabilities/pcb_aoi/usd_organization/requirements/namespace) | All contract attributes under `pcba:` in the nine recognized scopes; unknown scopes are advisory warnings. |
| UO.011 | [material-binding](/capabilities/pcb_aoi/usd_organization/requirements/material-binding) | Renderable meshes SHOULD bind a material of the role's class; `matClass` explicit on `pkg_*` / `fixture_*`, derived on `board_*`. |
| UO.012 | [packaging-relative](/capabilities/pcb_aoi/usd_organization/requirements/packaging-relative) | Relative, self-contained references; one board asset placed per position; shared prototypes with `instanceable = true`. |
| UO.013 | [package-manifest](/capabilities/pcb_aoi/usd_organization/requirements/package-manifest) | `pcba:board:packageManifest` inventory of packaged files for a distributed package. |
| UO.014 | [origin-convention](/capabilities/pcb_aoi/usd_organization/requirements/origin-convention) | `pcba:board:originConvention` from five tokens; `originPointMm` MUST when `datum_explicit`. |
| UO.015 | [provenance](/capabilities/pcb_aoi/usd_organization/requirements/provenance) | `pcba:board:generatorVersion` + `pcba:board:contentHash` on the board root, both MUST. |
| UO.016 | [file-naming](/capabilities/pcb_aoi/usd_organization/requirements/file-naming) | SHOULD: clean ASCII file names, no spaces or parentheses. |
| UO.017 | [role-material](/capabilities/pcb_aoi/usd_organization/requirements/role-material) | Where `pcba:mesh:role` determines the material class, the bound material MUST agree with it (checked by class). |

```{toctree}
:maxdepth: 1
:hidden:

requirements
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
