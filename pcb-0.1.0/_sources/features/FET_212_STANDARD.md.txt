# Feature: `FET_212_STANDARD`

| **Property** | **Value** |
|--------------|-----------|
| Feature Name | `FET_212_STANDARD` |
| Runtime | `STANDARD` |
| Proprietary Techs | `None` |
| Latest Version | `0.1.0` |
| Domain | PCB AOI (USD input contract) |

## Description

**PCB Component Geometry.** Where each placed component sits and how its package is built: side, nominal position and
rotation; the anchor convention and body centroid that relate the package mesh to the placement; body
height; pin count and pitch; per-pin geometry (number, solderability, cross-section, terminal type);
and pin-1 position for keyed parts.

The entity spans two prims: the **placement** (pose on the instance in the board file) and the
**package prototype** it references (body and pins, authored once and shared). Package meshes are found
by `pcba:mesh:role` (`pkg_body`, `pkg_lead`, …); pins carry `pcba:pin:*`. The rules descend into
referenced prototypes, so a defect inside a shared package fails every board that places it.

Components are discovered through their identity attributes, so this feature depends on
[`FET_211_STANDARD`](FET_211_STANDARD): without identity there is nothing for these rules to check.

Requirement levels follow the PCBA to USD Input Contract **1.0.2**. The entity this feature describes
is the **placed component and its package**. Fields whose upstream data is not yet available are declared with
`pcba:prov:<attr> = "not_yet_available"` and reported as declared gaps rather than failures.

## Dependency Graph

This feature depends on [`FET_211_STANDARD`](FET_211_STANDARD) (PCB Component Identity). It is depended on by [`FET_215_STANDARD`](FET_215_STANDARD) (PCB AOI Appearance). The six PCB features are composed by the [PCB-Assembly](../profiles/pcb_assembly) profile; the four that do not concern placed components also form [PCB-Board](../profiles/pcb_board).

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
    class FET_212 current
    class FET_211,FET_213,FET_214,FET_215,FET_216 other
```

## Use Cases

- AOI synthetic-data generation: locating every pin so solder and component defects can be simulated at the right joint.
- Placement verification against the design's nominal positions.
- Validation of board exports against the input contract before ingestion.

## Requirements

### Version 0.1.0
<details>
<summary><strong>Details</strong></summary>

#### Requirement List

* Capability: [PCB Component Geometry](../capabilities/pcb_aoi/component_geometry/capability-component_geometry)
    * [Placement](../capabilities/pcb_aoi/component_geometry/requirements/placement) — `CG.001`
    * [Anchor & Geometry Reference](../capabilities/pcb_aoi/component_geometry/requirements/anchor) — `CG.002`
    * [Body Height](../capabilities/pcb_aoi/component_geometry/requirements/body-height) — `CG.003`
    * [Pin Count](../capabilities/pcb_aoi/component_geometry/requirements/pin-count) — `CG.005`
    * [Pin Pitch](../capabilities/pcb_aoi/component_geometry/requirements/pin-pitch) — `CG.006`
    * [Pin Geometry](../capabilities/pcb_aoi/component_geometry/requirements/pin-geometry) — `CG.007`
    * [Pin-1 Position](../capabilities/pcb_aoi/component_geometry/requirements/pin1-position) — `CG.008`

`CG.018` (press-fit state) is documented in the capability but intentionally has no executable rule and is not part of the feature.

#### Used in Profiles

* [PCB-Assembly](../profiles/pcb_assembly) — version 0.1.0

</details>

## Pipelines

Source file type:

- `.usd`, `.usda`, `.usdc` board asset — normally several files (board, component prototypes,
  optionally a panel) linked by relative references / payloads, with no external dependencies.

Validation or runtime pipeline:

- **Static contract validation only.** The rules run over the composed stage, including every
  referenced prototype, and check attribute presence, vocabulary membership, pin-number uniqueness within a component, and
agreement between the declared pin count and the pin prims present, including inside referenced
prototypes. Advisory conditions are reported as warnings and
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

None is safe. Positions, rotations, pin numbers and pin geometry are source truth from the
CAD footprint and the package model; a repair cannot know where a pin is or which number it carries.

---

## Comments

**Known-missing convention:** a MUST field whose upstream data is not available yet MAY be omitted
if the prim carries `pcba:prov:<attr> = "not_yet_available"` (or `"source_data_required"` where
sourcing was attempted and failed). The rules report supported deferrals as declared gaps, not
failures. `simready-validate` filters declared gaps and advisories from its profile
results; use the contract's reference validator when all reporting buckets are needed, as described
in the [profile authoring guide](../profiles/pcb_assembly).
