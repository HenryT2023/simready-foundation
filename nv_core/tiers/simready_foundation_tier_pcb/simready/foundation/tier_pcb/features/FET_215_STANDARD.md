# Feature: `FET_215_STANDARD`

| **Property** | **Value** |
|--------------|-----------|
| Feature Name | `FET_215_STANDARD` |
| Runtime | `STANDARD` |
| Proprietary Techs | `None` |
| Latest Version | `0.1.0` |
| Domain | PCB AOI (USD input contract) |

## Description

**PCB AOI Appearance.** What a rendered board must look like for optical inspection: each placed component's
polarity type and markings where present, its nominal appearance (body colour, finish, material
class), a per-surface material class on every package mesh, a material binding on every package
mesh, and agreement between a mesh's role and the class of the material bound to it (copper geometry
is bound to a copper-class material, silkscreen to silkscreen, and so on).

The appearance rules read placed components (so they depend on
[`FET_212_STANDARD`](FET_212_STANDARD)) and mesh roles (so they depend on
[`FET_214_STANDARD`](FET_214_STANDARD)).

Requirement levels follow the PCBA to USD Input Contract **1.0.2**. The entity this feature describes
is **what the camera sees**. Fields whose upstream data is not yet available are declared with
`pcba:prov:<attr> = "not_yet_available"` and reported as declared gaps rather than failures.

## Dependency Graph

This feature depends on [`FET_212_STANDARD`](FET_212_STANDARD) (PCB Component Geometry) and [`FET_214_STANDARD`](FET_214_STANDARD) (PCB USD Core). The six PCB features are composed by the [PCB-Assembly](../profiles/pcb_assembly) profile; the four that do not concern placed components also form [PCB-Board](../profiles/pcb_board).

```{mermaid}
flowchart LR
    FET_211["FET_211_STANDARD\n0.1.0"]
    FET_212["FET_212_STANDARD\n0.1.0"]
    FET_213["FET_213_STANDARD\n0.1.0"]
    FET_214["FET_214_STANDARD\n0.1.0"]
    FET_215["FET_215_STANDARD\n0.1.0"]
    FET_216["FET_216_STANDARD\n0.1.0"]
    FET_212 --> FET_211
    FET_215 --> FET_212
    FET_215 --> FET_214

    classDef current fill:#90EE90,stroke:#333
    classDef other fill:#fff,stroke:#333
    class FET_215 current
    class FET_211,FET_212,FET_213,FET_214,FET_216 other
```

## Use Cases

- AOI synthetic-data generation: rendering boards with production-accurate colour, finish and material so generated images match camera captures.
- Detecting mis-tagged geometry (silkscreen tagged as copper) before it reaches a renderer.

## Requirements

### Version 0.1.0
<details>
<summary><strong>Details</strong></summary>

#### Requirement List

* Capability: [PCB Component Geometry](../capabilities/pcb_aoi/component_geometry/capability-component_geometry)
    * [Polarity](../capabilities/pcb_aoi/component_geometry/requirements/polarity) — `CG.009`
    * [Markings](../capabilities/pcb_aoi/component_geometry/requirements/markings) — `CG.010`
    * [Nominal Appearance](../capabilities/pcb_aoi/component_geometry/requirements/nominal-appearance) — `CG.011`
    * [Per-Surface Material](../capabilities/pcb_aoi/component_geometry/requirements/per-surface-material) — `CG.012`
* Capability: [PCB USD Organization](../capabilities/pcb_aoi/usd_organization/capability-usd_organization)
    * [Material Binding](../capabilities/pcb_aoi/usd_organization/requirements/material-binding) — `UO.011`
    * [Role/Material Consistency](../capabilities/pcb_aoi/usd_organization/requirements/role-material) — `UO.017`

#### Used in Profiles

* [PCB-Assembly](../profiles/pcb_assembly) — version 0.1.0
* [PCB-Board](../profiles/pcb_board) — version 0.1.0

</details>

## Pipelines

Source file type:

- `.usd`, `.usda`, `.usdc` board asset — normally several files (board, component prototypes,
  optionally a panel) linked by relative references / payloads, with no external dependencies.

Validation or runtime pipeline:

- **Static contract validation only.** The rules run over the composed stage, including every
  referenced prototype, and check attribute presence and vocabulary for the appearance fields, material-class vocabulary on
package meshes, presence of a direct material binding on package meshes, and role/material-class
agreement using direct, all-purpose bindings resolved in each placed context. Collection-based and
purpose-specific bindings are not resolved; the role/material check skips, never fails, meshes it
cannot resolve. Advisory conditions are reported as warnings and
  `pcba:prov:` deferrals as declared gaps.
- This gate does not render the board or evaluate AOI output. A pass means the implemented static
  checks found no reported failures; each requirement page states what its checker proves and what
  remains manual inspection.

## Samples

- `sample_content/pcb/board_min.usda` (with
  `protos/QFN8.usda` and `protos/HDR2.usda`) — the minimal conformant sample: one SMT part, one
  through-hole part, a fiducial, a mechanical part, and a no-stuff pad. Illustrative mesh geometry
  (points / faces) is omitted, so it is not a render or runtime acceptance test.
- `sample_content/pcb/board_bad_role.usda` — a negative
  sample with one mesh role outside the vocabulary (`UO.009`).

## Benchmarks

- None. Conformance is the static validation described above.

## Adapters

None.

## Automated repair

Not automated. Nominal colour, finish and material class are BOM truth; binding a material to
an unbound mesh or changing a mis-classed material is an authoring decision about how the part should
render, which a validator must not take on the exporter's behalf. A material class *derivable* from a
board role is already accepted without being authored.

---

## Comments

**Known-missing convention:** a MUST field whose upstream data is not available yet MAY be omitted
if the prim carries `pcba:prov:<attr> = "not_yet_available"` (or `"source_data_required"` where
sourcing was attempted and failed). The rules report supported deferrals as declared gaps, not
failures. `simready-validate` filters declared gaps and advisories from its profile
results; use the contract's reference validator when all reporting buckets are needed, as described
in the [profile authoring guide](../profiles/pcb_assembly).
