# Placement

| Code | CG.001 |
|------|------|
| Validator | `PlacementChecker` |
| Applies to | placed component prim (discovered by `pcba:component:*`) |
| Requirement level | MUST (`side` for every placement; `nominalPosMm` / `nominalRotationDeg` MUST for electrical parts, SHOULD for fiducial / mechanical) |
| Tags | `component`, `placement`, `orientation`, `ground-truth` |

## Summary

Every placed component prim MUST carry `pcba:component:side` (`top` \| `bottom`). Electrical
parts MUST also carry `pcba:component:nominalPosMm` (board-local x, y in mm) and
`pcba:component:nominalRotationDeg` (rotation about the board normal Z). For `fiducial` and
`mechanical` placements the pose fields are SHOULD.

This page follows PCBA to USD Input Contract **1.0.2**, sections 8 and 8.1.

## Description

Placement is the primary geometric ground truth the pipeline needs to seat a component and to
generate placement defects. `side` says which face the part is mounted on — it comes from this
attribute, never from which layer group the prim is nested under. `nominalPosMm` gives the
intended (x, y) of the component **anchor**
([CG.002](/capabilities/pcb_aoi/component_geometry/requirements/anchor)) in the board-local
frame, consistent with `metersPerUnit = 0.001`. `nominalRotationDeg` is the intended rotation
about Z.

These are the nominal (design-intent) values. The pipeline compares them against the as-placed
transform to author shift, rotation, tombstone, and missing-component ground truth. The prim's
USD transform MUST agree with these attributes through the declared anchor; no compensating
root scale or rotation is permitted
([UO.006](/capabilities/pcb_aoi/usd_organization/requirements/stage-conventions)).

A placed component is discovered by any of `pcba:component:refdes`, `instanceId`, or
`processClass` — never by prim name or path. Fiducials and mechanical parts still MUST state
`side` (a mis-sided fiducial must fail), but their pose fields are recommended rather than
gated.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:side` | `token` | MUST (all placements) | `top` \| `bottom`. |
| `pcba:component:nominalPosMm` | `float2` | MUST (electrical); SHOULD (fiducial / mechanical) | Board-local (x, y) of the anchor, mm. |
| `pcba:component:nominalRotationDeg` | `float` | MUST (electrical); SHOULD (fiducial / mechanical) | Rotation about the board normal Z, degrees. |

## Why is it required?

- Placement is the ground truth for the largest class of AOI defects (shift, rotation,
  tombstone, missing).
- Storing side, position, and rotation on the prim resolves placement without a separate
  placement-file join at ingest time.
- Millimetre units matched to `metersPerUnit = 0.001` make the values machine-checkable.

## Example

```usda
def Xform "U7" (
    instanceable = true
    prepend references = @./protos/QFN8.usda@</Proto>
)
{
    string pcba:component:refdes = "U7"
    token  pcba:component:side = "top"
    float2 pcba:component:nominalPosMm = (20.0, 30.0)
    float  pcba:component:nominalRotationDeg = 90.0
    double3 xformOp:translate = (20.0, 30.0, 0.0)
    float   xformOp:rotateZ = 90.0
    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateZ"]
}
```

## How to comply

- Author `side` on every placement and the two pose fields on every electrical part.
- Express position in board-local millimetres and rotation in degrees about Z.
- Keep the prim's transform consistent with these values through the declared anchor.

### What the checker proves

`PlacementChecker` fails any placed component whose `side` is absent or outside `top` /
`bottom`, and fails an electrical part missing `nominalPosMm` or `nominalRotationDeg` (a
`pcba:prov:` marker downgrades a missing field to a declared gap). Fiducial and mechanical
parts are exempt from the pose checks. It does not compare the values with the prim's
transform.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Anchor & Geometry Reference (CG.002)](/capabilities/pcb_aoi/component_geometry/requirements/anchor)
