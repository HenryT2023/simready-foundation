# Stage Conventions

| Code | UO.006 |
|------|------|
| Validator | `StageConventionsChecker` |
| Applies to | the board stage and its `defaultPrim` |
| Requirement level | MUST |
| Tags | `organization` |

## Summary

The board stage MUST use `metersPerUnit = 0.001` (mm) and `upAxis = "Z"`, with **no
compensating root scale or rotation** on the default prim. The board lies in the **XY plane with
+Z as the board normal**: component height is +Z, `pcba:component:heightMm` is the Z extent, and
`pcba:component:nominalRotationDeg` is about Z.

This page follows PCBA to USD Input Contract **1.0.2**, section 2.

## Description

Placement, height, and rotation metadata are only meaningful against a fixed frame, so the
conventions are pinned:

- **`metersPerUnit = 0.001`** — the stage is authored in millimetres.
- **`upAxis = "Z"`** — the board lies in XY; Z is the board normal. Bodies rise in +Z.
- **No compensating root transform.** Do not author a Y-up tag and cancel it with a root
  rotation, or author metres and cancel with a root scale. Author the geometry Z-up in mm.
- Component transforms use `pcba:component:anchor` and agree with `nominalPosMm` /
  `nominalRotationDeg` ([CG.001](/capabilities/pcb_aoi/component_geometry/requirements/placement)).

A single `defaultPrim` is required; its name is free
([UO.001](/capabilities/pcb_aoi/usd_organization/requirements/board-root)).

> **Note on the code.** `UO.006` numbers the stage-conventions rule so it is addressable
> alongside the rest of the UO set; the source requirements have no separately numbered line
> for it.

## Fields

| Metadata | Value | Req | Notes |
|----------|-------|-----|-------|
| `metersPerUnit` | `0.001` | MUST | Stage authored in mm; no compensating root scale. |
| `upAxis` | `"Z"` | MUST | Board in the XY plane, Z normal; no compensating root rotation. |
| `defaultPrim` | any valid identifier | MUST | Single default prim; Xformable, with no scale/rotate xformOps. |

## Why is it required?

- mm + Z-up makes every consumer interpret placement, height, and rotation the same way
  without per-asset calibration.
- A compensating root transform hides a unit or axis mismatch that then surfaces as
  mis-seated geometry downstream.

## Example

```usda
#usda 1.0
(
    defaultPrim = "Board"
    metersPerUnit = 0.001
    upAxis = "Z"
)

def Xform "Board"
{
    # board lies in XY; Z is the board normal — no compensating root scale/rotation
    float pcba:board:thicknessMm = 1.6
}
```

## How to comply

- Set `metersPerUnit = 0.001` and `upAxis = "Z"` in the stage metadata.
- Author geometry directly in mm, XY plane, Z normal; add no root scale or rotation to
  "correct" units or orientation.
- Keep component transforms consistent with the declared anchor and nominal placement.

### What the checker proves

`StageConventionsChecker` fails when `metersPerUnit` is not 0.001, when `upAxis` is not `Z`,
when the stage has no `defaultPrim`, or when the default prim's xformOp order contains a scale
or rotate op. It does not check that geometry actually lies in XY or that component transforms
agree with their nominal placement.

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Board Root (UO.001)](/capabilities/pcb_aoi/usd_organization/requirements/board-root)
