# Feature: `FET_213_STANDARD`

| **Property** | **Value** |
|--------------|-----------|
| Feature Name | `FET_213_STANDARD` |
| Runtime | `STANDARD` |
| Proprietary Techs | `None` |
| Latest Version | `0.1.0` |
| Domain | PCB AOI (USD input contract) |

## Description

**PCB Board Geometry.** The fabricated board itself: its thickness; copper and solder-mask geometry; individually
addressable pads with pad numbers; solder-paste deposits with their side and the contact they are for;
plated barrels at every occupied through-hole joint; hole geometry on those barrels; and, for every
pad and barrel, its occupancy state and the association to the component terminal that lands on it.

Board geometry is found by `pcba:mesh:role` (`board_substrate`, `board_copper`, `board_mask`,
`board_pad`, `board_paste`, `board_barrel`, `board_hole`, …). Associations are authored
**board-side** as the `pcba:board:refdes` + `pcba:board:componentPinNumber` pair, and a no-stuff site
says so with `pcba:board:intentionallyUnpopulated`. Where components are present on the stage the
association is also resolved against them (the named pin must exist; a surface-mount pad must sit at
the pin it names). On a bare board with no components those cross-checks are skipped, not failed, so
this feature has no hard dependency on the component features.

Requirement levels follow the PCBA to USD Input Contract **1.0.2**. The entity this feature describes
is the **board**. Fields whose upstream data is not yet available are declared with
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
    class FET_213 current
    class FET_211,FET_212,FET_214,FET_215,FET_216 other
```

## Use Cases

- AOI synthetic-data generation: deriving joint regions of interest from pads, barrels and paste, and distinguishing a no-stuff site from a missing component.
- Bare-board hand-off from a fabrication or CAD export ahead of component data.
- Validation of board exports against the input contract before ingestion.

## Requirements

### Version 0.1.0
<details>
<summary><strong>Details</strong></summary>

#### Requirement List

* Capability: [PCB Board Geometry](../capabilities/pcb_aoi/board_geometry/capability-board_geometry)
    * [Board Thickness](../capabilities/pcb_aoi/board_geometry/requirements/board-thickness) — `BG.001`
    * [Copper and Solder-Mask Geometry](../capabilities/pcb_aoi/board_geometry/requirements/copper-mask-geometry) — `BG.002`
    * [Plated Barrel at Occupied Through-Hole Joints](../capabilities/pcb_aoi/board_geometry/requirements/hole-plating) — `BG.003`
    * [Pad Number](../capabilities/pcb_aoi/board_geometry/requirements/pad-number) — `BG.005`
    * [Paste Association](../capabilities/pcb_aoi/board_geometry/requirements/paste-association) — `BG.007`
    * [Paste Side](../capabilities/pcb_aoi/board_geometry/requirements/paste-side) — `BG.008`
    * [Hole and Pad Geometry](../capabilities/pcb_aoi/board_geometry/requirements/hole-and-pad-geometry) — `BG.010`
    * [Hole Occupancy and Pin Association](../capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy) — `BG.012`

`BG.014` (paste-in-hole) is documented in the capability but intentionally has no executable rule and is not part of the feature.

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
  referenced prototype, and check attribute presence, vocabulary membership, and internal consistency (that a pad's
`componentPinNumber` resolves to a pin of the named component, that at most one pad per side and one
barrel claim a joint, and that a surface-mount pad sits at the pin it claims when `extent` geometry
is present). A joint is a solderable or press-fit pin; locating pegs owe no barrel. Advisory conditions are reported as warnings and
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

None is safe. Pad numbers, occupancy and pin associations are source truth; a repair that
guesses which terminal lands on a pad would place simulated solder on the wrong joint, which is the
exact failure the contract exists to prevent.

---

## Comments

**Known-missing convention:** a MUST field whose upstream data is not available yet MAY be omitted
if the prim carries `pcba:prov:<attr> = "not_yet_available"` (or `"source_data_required"` where
sourcing was attempted and failed). The rules report supported deferrals as declared gaps, not
failures. `simready-validate` filters declared gaps and advisories from its profile
results; use the contract's reference validator when all reporting buckets are needed, as described
in the [profile authoring guide](../profiles/pcb_assembly).
