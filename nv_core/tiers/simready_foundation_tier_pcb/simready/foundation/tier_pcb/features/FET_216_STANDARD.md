# Feature: `FET_216_STANDARD`

| **Property** | **Value** |
|--------------|-----------|
| Feature Name | `FET_216_STANDARD` |
| Runtime | `STANDARD` |
| Proprietary Techs | `None` |
| Latest Version | `0.1.0` |
| Domain | PCB AOI (USD input contract) |

## Description

**PCB Delivery Package.** What makes a board export a relocatable, traceable package: every reference and payload
resolves and uses a relative asset path; the board root declares a package manifest (the inventory of
files the package contains); provenance names the generator and a content hash; and file names are
clean ASCII without spaces or parentheses.

These are the rules a receiving pipeline checks before it opens anything else, and the ones an
exporter can satisfy without knowing anything about the board.

Requirement levels follow the PCBA to USD Input Contract **1.0.2**. The entity this feature describes
is **the delivered file set**. Fields whose upstream data is not yet available are declared with
`pcba:prov:<attr> = "not_yet_available"` and reported as declared gaps rather than failures.

## Dependency Graph

This feature has no feature dependencies. The six PCB features are composed by the [PCB-Assembly](../profiles/pcb_assembly) profile; the four that do not concern placed components also form [PCB-Board](../profiles/pcb_board).

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
    class FET_216 current
    class FET_211,FET_212,FET_213,FET_214,FET_215 other
```

## Use Cases

- Hand-off of a board package between tools and sites without broken references.
- Tracing a delivered asset back to the tool and source data that produced it.

## Requirements

### Version 0.1.0
<details>
<summary><strong>Details</strong></summary>

#### Requirement List

* Capability: [PCB USD Organization](../capabilities/pcb_aoi/usd_organization/capability-usd_organization)
    * [Packaging Relative](../capabilities/pcb_aoi/usd_organization/requirements/packaging-relative) — `UO.012`
    * [Package Manifest](../capabilities/pcb_aoi/usd_organization/requirements/package-manifest) — `UO.013`
    * [Provenance](../capabilities/pcb_aoi/usd_organization/requirements/provenance) — `UO.015`
    * [File Naming](../capabilities/pcb_aoi/usd_organization/requirements/file-naming) — `UO.016`

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
  referenced prototype, and check composition errors, absolute asset paths, presence of the manifest, provenance and
provenance content, and file-name characters across every layer the stage uses. Advisory conditions are reported as warnings and
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

Partly safe, and the one PCB feature where a conform skill is worthwhile: rewriting an absolute
asset path to a relative one when the target exists, renaming a file with spaces and updating the
references to it, and authoring a manifest from the delivered file inventory are mechanical and
reversible. Provenance values must not be invented. A conform skill for this feature is a planned
follow-up.

---

## Comments

**Known-missing convention:** a MUST field whose upstream data is not available yet MAY be omitted
if the prim carries `pcba:prov:<attr> = "not_yet_available"` (or `"source_data_required"` where
sourcing was attempted and failed). The rules report supported deferrals as declared gaps, not
failures. `simready-validate` filters declared gaps and advisories from its profile
results; use the contract's reference validator when all reporting buckets are needed, as described
in the [profile authoring guide](../profiles/pcb_assembly).
