# Feature: `FET_214_STANDARD`

| **Property** | **Value** |
|--------------|-----------|
| Feature Name | `FET_214_STANDARD` |
| Runtime | `STANDARD` |
| Proprietary Techs | `None` |
| Latest Version | `0.1.0` |
| Domain | PCB AOI (USD input contract) |

## Description

**PCB USD Core.** How a board USD is put together so a consumer can find everything by attribute and role: a
single default prim and a board root discoverable by its `pcba:board:*` metadata; a `board_substrate`
mesh; the stage conventions (`upAxis = Z`, `metersPerUnit = 0.001`, no compensating root transform);
a mesh-role token from the contract vocabulary on every `Mesh`; the `pcba:` namespace convention; and
the board's origin convention.

This is the base every other PCB feature stands on: roles are how geometry is found, the board root
is how a board is found, and the stage conventions are what make positions mean millimetres.

Requirement levels follow the PCBA to USD Input Contract **1.0.2**. The entity this feature describes
is the **board file as a whole**. Fields whose upstream data is not yet available are declared with
`pcba:prov:<attr> = "not_yet_available"` and reported as declared gaps rather than failures.

## Dependency Graph

This feature has no feature dependencies. It is depended on by [`FET_215_STANDARD`](FET_215_STANDARD) (PCB AOI Appearance). The six PCB features are composed by the [PCB-Assembly](../profiles/pcb_assembly) profile; the four that do not concern placed components also form [PCB-Board](../profiles/pcb_board).

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
    class FET_214 current
    class FET_211,FET_212,FET_213,FET_215,FET_216 other
```

## Use Cases

- Ingestion of board exports by any consumer that must locate geometry and metadata without knowledge of the exporter's prim naming.
- Validation of board exports against the input contract before ingestion.

## Requirements

### Version 0.1.0
<details>
<summary><strong>Details</strong></summary>

#### Requirement List

* Capability: [PCB USD Organization](../capabilities/pcb_aoi/usd_organization/capability-usd_organization)
    * [Board Root](../capabilities/pcb_aoi/usd_organization/requirements/board-root) — `UO.001`
    * [Stage Layout](../capabilities/pcb_aoi/usd_organization/requirements/stage-layout) — `UO.003`
    * [Stage Conventions](../capabilities/pcb_aoi/usd_organization/requirements/stage-conventions) — `UO.006`
    * [Mesh Role](../capabilities/pcb_aoi/usd_organization/requirements/mesh-role) — `UO.009`
    * [Namespace](../capabilities/pcb_aoi/usd_organization/requirements/namespace) — `UO.010`
    * [Origin Convention](../capabilities/pcb_aoi/usd_organization/requirements/origin-convention) — `UO.014`

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
  referenced prototype, and check stage metadata, default prim and board-root discovery, mesh-role presence and vocabulary,
attribute namespaces, and the origin convention. Advisory conditions are reported as warnings and
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

None is safe. Rescaling or re-orienting a stage to satisfy the unit and axis conventions would
silently change every coordinate the asset carries, and a mesh's role cannot be inferred from its
geometry. Reporting only.

---

## Comments

**Known-missing convention:** a MUST field whose upstream data is not available yet MAY be omitted
if the prim carries `pcba:prov:<attr> = "not_yet_available"` (or `"source_data_required"` where
sourcing was attempted and failed). The rules report supported deferrals as declared gaps, not
failures. `simready-validate` filters declared gaps and advisories from its profile
results; use the contract's reference validator when all reporting buckets are needed, as described
in the [profile authoring guide](../profiles/pcb_assembly).
