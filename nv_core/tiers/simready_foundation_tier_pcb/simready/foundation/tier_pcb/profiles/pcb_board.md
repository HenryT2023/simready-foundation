# PCB-Board Profile USD Authoring Guide

This document describes how to author a USD asset that conforms to the `PCB-Board` profile:
the **board-level subset** of the PCB contract — the fabricated board's geometry, the USD core
conventions, appearance, and delivery packaging — without the two features that describe placed
components.

`PCB-Board` is what a **bare (unpopulated) board** is validated against. It is a subset of
[`PCB-Assembly`](pcb_assembly), so a populated board that passes `PCB-Assembly` also passes
`PCB-Board`; the profile does not forbid components, it simply does not check them. Use it for
a board asset that exists without, or ahead of, its component data, whatever produced it.

## Profile definition

Profile `0.1.0` implements the board-level parts of the **PCB to USD input contract v1.0.2**. Wheel
`0.1.0a1`, the features and the contract have separate version identifiers; the contract's document
version is not the `--version` argument.

```toml
[PCB-Board]
"0.1.0" = {features = [
    {"FET_213_STANDARD" = {version = "0.1.0"}}, # "PCB Board Geometry"
    {"FET_214_STANDARD" = {version = "0.1.0"}}, # "PCB USD Core"
    {"FET_215_STANDARD" = {version = "0.1.0"}}, # "PCB AOI Appearance"
    {"FET_216_STANDARD" = {version = "0.1.0"}}, # "PCB Delivery Package"
]}
```

| Feature | Codes | What it governs |
|---|---|---|
| [FET_213_STANDARD — PCB Board Geometry](../features/FET_213_STANDARD) | `BG.001`, `BG.002`, `BG.003`, `BG.005`, `BG.007`, `BG.008`, `BG.010`, `BG.012` | board thickness, copper and mask geometry, barrels at through-hole joints, pad numbers, paste association and side, hole geometry, site occupancy and pin↔pad association |
| [FET_214_STANDARD — PCB USD Core](../features/FET_214_STANDARD) | `UO.001`, `UO.003`, `UO.006`, `UO.009`, `UO.010`, `UO.014` | board root and stage layout, stage conventions (Z-up, millimetres), mesh roles, the `pcba:` namespace, origin convention |
| [FET_215_STANDARD — PCB AOI Appearance](../features/FET_215_STANDARD) | `CG.009`, `CG.010`, `CG.011`, `CG.012`, `UO.011`, `UO.017` | polarity, markings, nominal appearance, per-surface material class, material binding, role/material consistency |
| [FET_216_STANDARD — PCB Delivery Package](../features/FET_216_STANDARD) | `UO.012`, `UO.013`, `UO.015`, `UO.016` | relative self-contained references, package manifest, provenance, file naming |

## What a conformant asset looks like

- **One self-contained USD asset** with **relative** references only and no external dependencies,
  a package manifest, provenance, and clean ASCII file names.
- **Discovery is by attribute and role, never by prim name or hierarchy position.** The board root
  is found by its `pcba:board:*` attributes; every geometry `Mesh` carries a `pcba:mesh:role` token
  from the fixed vocabulary (`board_substrate`, `board_copper`, `board_mask`, `board_pad`,
  `board_paste`, `board_barrel`, `board_hole`, …).
- **Stage conventions:** `upAxis = Z`, `metersPerUnit = 0.001` (millimetres), board in the XY plane
  with Z as its normal, no compensating root transform.
- **Sites state their occupancy.** Every `board_pad` and `board_barrel` carries
  `pcba:board:occupied`. An occupied site names the component terminal that will land on it
  (`pcba:board:refdes` + `pcba:board:componentPinNumber`); an unoccupied pad states whether it is
  a no-stuff site (`pcba:board:intentionallyUnpopulated`). Occupancy not yet known is declared with
  `pcba:prov:occupied`.
- **Materials agree with roles.** A mesh bound to a material is bound to one whose class matches its
  role (copper geometry to a copper-class material, and so on).
- **No components required.** Checks that resolve an association against a component's pins, or
  require a barrel for a placed through-hole part, are skipped when the stage carries no
  components. They apply in full once the board is populated and validated as `PCB-Assembly`.

## Known-missing fields

A MUST field whose upstream data is not available yet MAY be omitted, provided the prim carries
`pcba:prov:<attr> = "not_yet_available"` (or `"source_data_required"` where sourcing was attempted
and failed). The PCB rules emit these as INFO **declared gaps**, separately from WARNING advisories
and failures.

**Reporting limitation:** `simready-validate` filters INFO and WARNING issues out of its
returned profile results. Its PASS cannot establish that no declared gaps or advisories remain. To
retain all three buckets, use the contract's reference validator.

## Validate

```bash
simready-validate --profile PCB-Board --version 0.1.0 board.usda -v
```

Select the profile explicitly as above; `pcba:*` attributes alone do not select it.

## Relationship to SimReady core

The profile shares core's `upAxis = Z` convention (`UN.006`) but its millimetre stage
(`metersPerUnit = 0.001`) differs from core's `UN.007` (`metersPerUnit = 1.0`), so it does not
include core's Minimal Placeable Visual feature (`FET_001_STANDARD`).
