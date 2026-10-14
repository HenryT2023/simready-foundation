# Board Root

| Code | UO.001 |
|------|------|
| Validator | `BoardRootChecker` |
| Applies to | the stage `defaultPrim` and the board-root prim (discovered by `pcba:board:*`) |
| Requirement level | MUST |
| Tags | `organization` |

## Summary

The board asset MUST have a single `defaultPrim` — its **name is free** — and MUST contain a
board-root prim discoverable by its `pcba:board:*` attributes, which carry the board-level
metadata (provenance, packaging, thickness, origin convention). The board root MAY be the
default prim but need not be.

This page follows PCBA to USD Input Contract **1.0.2**, sections 2, 3 and 11.

## Description

Consumers read `defaultPrim` programmatically, so its name is any valid identifier. **Discovery
is by attribute, never by prim name or position**: the board root is the prim carrying
`pcba:board:*` root metadata. Three arrangements are all conformant:

- a bare board whose default prim *is* the board root;
- a stage whose default prim is a scene wrapper (e.g. a `/World` holding cameras and lights)
  with the board prim beneath it;
- a panel whose board master is a `class` prim referenced once per position — the master's
  `pcba:board:*` values resolve on every position, authored once.

`pcba:board:name` (OPTIONAL, human-readable board name) is **board-root only** and MUST NOT be
repeated on child prims — keep vendor names and part numbers out of the prim hierarchy. A
panel position resolving the master's `name` through its reference is not a repetition.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:board:generatorVersion` | `string` | MUST | Exporter / generator version (UO.015). |
| `pcba:board:contentHash` | `string` | MUST | Content hash of referenced assets (UO.015). |
| `pcba:board:packageManifest` | `asset` | MUST for a distributed package | Inventory of packaged files (UO.013). |
| `pcba:board:thicknessMm` | `float` | MUST | Pressed board thickness, mm (BG.001). |
| `pcba:board:originConvention` | `token` | MUST | `cad_bbox_lower_left \| fiducial_f1 \| mounting_hole \| datum_explicit \| unspecified` (UO.014). |
| `pcba:board:originPointMm` | `float2` | MUST when `originConvention = datum_explicit` | The datum in board-local mm (UO.014). |
| `pcba:board:originLabel` | `string` | SHOULD | Name of the datum feature, e.g. `MH1`. |
| `pcba:board:partNumber` | `string` | SHOULD | The board's own part number. |
| `pcba:board:variant` | `string` | SHOULD | Board variant / SKU id. |
| `pcba:board:name` | `string` | OPTIONAL | Human-readable board name. Board-root only. |

## Why is it required?

- Every consumer needs one entry point (`defaultPrim`) and one place to find board-level
  metadata; attribute-based discovery keeps that independent of how an exporter names or nests
  its prims.
- A panel legitimately has several board roots sharing one master; discovery by attribute is
  what makes that work.

## Example

```usda
#usda 1.0
(
    defaultPrim = "Board"       # any valid identifier
    metersPerUnit = 0.001
    upAxis = "Z"
)

def Xform "Board" (
    kind = "component"
)
{
    string pcba:board:generatorVersion = "example_pcb_export 1.4.2"
    string pcba:board:contentHash = "sha256:0000…"
    asset  pcba:board:packageManifest = @./package_manifest.json@
    float  pcba:board:thicknessMm = 1.6
    token  pcba:board:originConvention = "datum_explicit"
    float2 pcba:board:originPointMm = (5.0, 5.0)
    string pcba:board:originLabel = "MH1"
    string pcba:board:name = "DEMO-BOARD-A"      # optional, board-root only
}
```

## How to comply

- Set a single `defaultPrim`; name it freely.
- Author the `pcba:board:*` metadata on the board prim itself, whether it is the default prim,
  a child of a wrapper, or a panel's class master.
- Author `pcba:board:name` on the board root only.

### What the checker proves

`BoardRootChecker` fails when the stage has no `defaultPrim` or it is not Xformable, and when no
prim carries a board-root `pcba:board:*` marker (`thicknessMm`, `originConvention`,
`generatorVersion`, `contentHash`, `packageManifest`, `name`, `variant`, `partNumber`). It warns
when `pcba:board:name` appears on a non-instance prim other than the board root. The individual
root attributes are checked by BG.001, UO.013, UO.014 and UO.015.

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Stage Layout (UO.003)](/capabilities/pcb_aoi/usd_organization/requirements/stage-layout)
