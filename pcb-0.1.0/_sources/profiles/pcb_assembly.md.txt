# PCB-Assembly Profile USD Authoring Guide

This document describes how to author a USD asset that conforms to the `PCB-Assembly` profile:
a **populated circuit board assembly (PCBA)** — a board with its components placed — represented
in USD so that every component, pin, pad and hole can be discovered by attribute and role.

The profile describes the **asset**, not a pipeline stage. It applies to any PCB assembly USD
whatever produced it: a CAD or process-preparation exporter, a board-building tool, or a script
that composes an assembly from a board and component packages. The motivating consumer is an AOI
(automated optical inspection) synthetic-data pipeline that renders the board and simulates solder
and component defects, but the rules read only the asset. It composes six features: who the parts
are, where they sit and how their packages are built, what the board itself carries, how the USD
file is organised, what the camera sees, and how the file set is packaged. The four features that
do not concern placed components also form [`PCB-Board`](pcb_board), the board-level subset.

## Profile definition

Profile `0.1.0` implements the **PCB to USD input contract v1.0.2**.
Wheel `0.1.0a1`, the features and the contract have separate version identifiers; the
contract's document version is not the `--version` argument.

```toml
[PCB-Assembly]
"0.1.0" = {features = [
    {"FET_211_STANDARD" = {version = "0.1.0"}}, # "PCB Component Identity"
    {"FET_212_STANDARD" = {version = "0.1.0"}}, # "PCB Component Geometry"
    {"FET_213_STANDARD" = {version = "0.1.0"}}, # "PCB Board Geometry"
    {"FET_214_STANDARD" = {version = "0.1.0"}}, # "PCB USD Core"
    {"FET_215_STANDARD" = {version = "0.1.0"}}, # "PCB AOI Appearance"
    {"FET_216_STANDARD" = {version = "0.1.0"}}, # "PCB Delivery Package"
]}
```

The six features together carry all 38 enforced requirements:

| Feature | Codes | What it governs |
|---|---|---|
| [FET_211_STANDARD — PCB Component Identity](../features/FET_211_STANDARD) | `CI.001`, `CI.002`, `CI.003`, `CI.004`, `CI.005`, `CI.006`, `UO.008` | refdes uniqueness, component type and process class vocabularies, package type, footprint id, part identity, the component registry |
| [FET_212_STANDARD — PCB Component Geometry](../features/FET_212_STANDARD) | `CG.001`, `CG.002`, `CG.003`, `CG.005`, `CG.006`, `CG.007`, `CG.008` | placement, anchor, body height, pin count, pitch and geometry, pin-1 position |
| [FET_213_STANDARD — PCB Board Geometry](../features/FET_213_STANDARD) | `BG.001`, `BG.002`, `BG.003`, `BG.005`, `BG.007`, `BG.008`, `BG.010`, `BG.012` | board thickness, copper and mask geometry, barrels at through-hole joints, pad numbers, paste association and side, hole geometry, site occupancy and pin↔pad association |
| [FET_214_STANDARD — PCB USD Core](../features/FET_214_STANDARD) | `UO.001`, `UO.003`, `UO.006`, `UO.009`, `UO.010`, `UO.014` | board root and stage layout, stage conventions (Z-up, millimetres), mesh roles, the `pcba:` namespace, origin convention |
| [FET_215_STANDARD — PCB AOI Appearance](../features/FET_215_STANDARD) | `CG.009`, `CG.010`, `CG.011`, `CG.012`, `UO.011`, `UO.017` | polarity, markings, nominal appearance, per-surface material class, material binding, role/material consistency |
| [FET_216_STANDARD — PCB Delivery Package](../features/FET_216_STANDARD) | `UO.012`, `UO.013`, `UO.015`, `UO.016` | relative self-contained references, package manifest, provenance, file naming |

Feature dependencies: `FET_212_STANDARD` depends on `FET_211_STANDARD` (components are discovered
through their identity attributes); `FET_215_STANDARD` depends on `FET_212_STANDARD` and
`FET_214_STANDARD`. The others stand alone.

There is no standalone component profile. The contract puts a component's identity and placement
on the instance in the board file, not on the shared package prototype, so a prototype file alone
carries geometry but no identity and cannot be validated as a component by itself.

## What a conformant asset looks like

- **One self-contained USD asset** — a single logical board, normally several files (board,
  component prototypes, optionally a panel) linked by **relative** references/payloads, with no
  external dependencies.
- **Discovery is by attribute and role, never by prim name or hierarchy position.** The board root
  is found by its `pcba:board:*` attributes (it may but need not be the default prim); every
  geometry `Mesh` carries a `pcba:mesh:role` token from a fixed vocabulary (`board_pad`,
  `board_barrel`, `pkg_body`, `pkg_lead`, …); components carry `pcba:component:*` identity and
  placement; pins carry `pcba:pin:*`.
- **Stage conventions:** `upAxis = Z`, `metersPerUnit = 0.001` (millimetres), board in the XY plane
  with Z as its normal, no compensating root transform.
- **Associations are authored board-side:** each occupied pad or barrel names the component
  terminal that lands on it (`pcba:board:refdes` + `pcba:board:componentPinNumber`), and the pad
  must sit at the pin it names. A through-hole joint is three prims — top ring, solder-side ring,
  barrel — all carrying the same association.
- **Prototype-and-reference composition:** repeated parts reference a shared prototype
  (`instanceable = true`); package-level data lives on the prototype, placement on the instance.

## Known-missing fields

A MUST field whose upstream data is not available yet MAY be omitted, provided the prim carries
`pcba:prov:<attr> = "not_yet_available"` (or `"source_data_required"` where sourcing was attempted
and failed). The PCB rules emit these as INFO **declared gaps**, separately from
WARNING advisories and failures. A waiver records unavailable data; it does not
establish that the missing information is safe for a downstream consumer to ignore.

**Reporting limitation:** `simready-validate` filters INFO and WARNING
issues out of its returned profile results. Its PASS cannot establish that no
declared gaps or advisories remain. To retain all three buckets, use the contract's
reference validator, which reports failures, declared gaps and warnings separately.

## Validate

```bash
simready-validate --profile PCB-Assembly --version 0.1.0 board.usda -v
```

Build/install prerequisites and the verified tier-aware validator prerelease are
documented in the PCB tier's repository `README.md`. Older 2026.4.x validators do
not discover tier content. Select the profile explicitly as above unless the
asset carries `customLayerData.SimReady_Metadata.validation` profile metadata;
`pcba:*` attributes alone do not select it.

The minimal metadata fixture has no blocking failures. Any advisory findings are
visible only through a reporter that retains them. The same board authored as a
`class` master placed twice on a panel exercises abstract-master discovery; it is
not proof of every panel composition pattern or render/runtime readiness.

## Relationship to SimReady core

The profile shares core's `upAxis = Z` convention (`UN.006`) but its millimetre stage
(`metersPerUnit = 0.001`) differs from core's `UN.007` (`metersPerUnit = 1.0`), so it does not
include core's Minimal Placeable Visual feature (`FET_001_STANDARD`). Which core requirements the
profile adopts directly is an open design question.
