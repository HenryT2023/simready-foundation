# Feature: `FET_211_STANDARD`

| **Property** | **Value** |
|--------------|-----------|
| Feature Name | `FET_211_STANDARD` |
| Runtime | `STANDARD` |
| Proprietary Techs | `None` |
| Latest Version | `0.1.0` |
| Domain | PCB AOI (USD input contract) |

## Description

**PCB Component Identity.** Every placed component on a populated circuit board (PCBA) is addressable and
describable: it carries a unique reference designator (or a stable instance id for parts that have
none), a component type and process class from the contract vocabularies, a package type, a footprint
id, and the two independent part-identity groups (manufacturer part number and manufacturer; value
and tolerance). The board's component registry (`pcba:board:members`) indexes them.

Identity is authored on the placement prim in the board file, not on the shared package prototype it
references, so one prototype can serve many placements. A component is discovered by attribute
(`pcba:component:refdes`, `pcba:component:processClass`, or `pcba:component:instanceId`), never by
prim name or hierarchy position. Fiducials and mechanical parts carry a reduced identity set.

Requirement levels follow the PCBA to USD Input Contract **1.0.2**. The entity this feature describes
is the **placed component**. Fields whose upstream data is not yet available are declared with
`pcba:prov:<attr> = "not_yet_available"` and reported as declared gaps rather than failures.

## Dependency Graph

This feature has no feature dependencies. It is depended on by [`FET_212_STANDARD`](FET_212_STANDARD) (PCB Component Geometry). The six PCB features are composed by the [PCB-Assembly](../profiles/pcb_assembly) profile; the four that do not concern placed components also form [PCB-Board](../profiles/pcb_board).

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
    class FET_211 current
    class FET_212,FET_213,FET_214,FET_215,FET_216 other
```

## Use Cases

- AOI synthetic-data generation: naming every part on the board so defects can be injected and labelled per reference designator.
- Bill-of-materials reconciliation between the exported board and the design or process data.
- Indexing a board's parts without a full stage traversal.

## Requirements

### Version 0.1.0
<details>
<summary><strong>Details</strong></summary>

#### Requirement List

* Capability: [PCB Component Identity](../capabilities/pcb_aoi/component_identity/capability-component_identity)
    * [Refdes Identity](../capabilities/pcb_aoi/component_identity/requirements/refdes-identity) — `CI.001`
    * [Component Type](../capabilities/pcb_aoi/component_identity/requirements/component-type) — `CI.002`
    * [Process Class](../capabilities/pcb_aoi/component_identity/requirements/process-class) — `CI.003`
    * [Package Type](../capabilities/pcb_aoi/component_identity/requirements/package-type) — `CI.004`
    * [Footprint Id](../capabilities/pcb_aoi/component_identity/requirements/footprint-id) — `CI.005`
    * [Part Identity](../capabilities/pcb_aoi/component_identity/requirements/part-identity) — `CI.006`
* Capability: [PCB USD Organization](../capabilities/pcb_aoi/usd_organization/capability-usd_organization)
    * [Registries](../capabilities/pcb_aoi/usd_organization/requirements/registries) — `UO.008`

`CI.007` (component manifest) is documented in the capability but intentionally has no executable rule and is not part of the feature.

#### Used in Profiles

* [PCB-Assembly](../profiles/pcb_assembly) — version 0.1.0

</details>

## Pipelines

Source file type:

- `.usd`, `.usda`, `.usdc` board asset — normally several files (board, component prototypes,
  optionally a panel) linked by relative references / payloads, with no external dependencies.

Validation or runtime pipeline:

- **Static contract validation only.** The rules run over the composed stage, including every
  referenced prototype, and check attribute presence, vocabulary membership, uniqueness of reference designators within
one board, and agreement between the registry and the placed components. Advisory conditions are reported as warnings and
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

None is safe. Reference designators, part numbers, package and footprint identifiers are
CAD and BOM truth; a repair that invents or renames them changes what the board *is*. Automated
conformance is limited to reporting.

---

## Comments

**Known-missing convention:** a MUST field whose upstream data is not available yet MAY be omitted
if the prim carries `pcba:prov:<attr> = "not_yet_available"` (or `"source_data_required"` where
sourcing was attempted and failed). The rules report supported deferrals as declared gaps, not
failures. `simready-validate` filters declared gaps and advisories from its profile
results; use the contract's reference validator when all reporting buckets are needed, as described
in the [profile authoring guide](../profiles/pcb_assembly).
