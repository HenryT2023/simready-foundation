# Body Height

| Code | CG.003 |
|------|------|
| Validator | `BodyHeightChecker` |
| Applies to | `placed component prim` and its body `Mesh` |
| Requirement level | MUST for `heightMm` (N/A for `fiducial` / `mechanical`); body `extent` recommended |
| Tags | `component`, `geometry`, `bounds`, `ground-truth` |

## Summary

Every electrical component MUST carry `pcba:component:heightMm` (the Z extent of the
component in millimetres, greater than zero). The body mesh should also carry a standard USD
`extent`, which the board-side geometric cross-checks rely on. Together they provide height and
world-bounds ground truth.

This page follows PCBA to USD Input Contract **1.0.2**, section 8.

## Description

`pcba:component:heightMm` is the component's extent along the board normal (Z),
in millimetres. It is the ground truth for height-related defects — a lifted
part, an incorrectly seated part, or a wrong-height substitution — and lets the
pipeline reason about the tallest features on a board without loading geometry.

The body mesh should additionally carry the standard USD `extent` attribute (the
local-space bounding box), so world-space bounds are computable through
`UsdGeom.BBoxCache` in the usual way, and so association-vs-geometry checks (BG.012) and the
contoured-hole derivation (BG.010) have geometry to work from. `heightMm` is the semantic,
mm-valued height ground truth; `extent` is the render/loader bounding box. The pipeline does not
infer one from the other.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:heightMm` | `float` | MUST | Z extent of the component, in mm |
| `extent` | `float3[]` (standard USD) | recommended | Local-space bounding box on the body mesh; world bounds via `UsdGeom.BBoxCache` |

## Why is it required?

- Height is the ground truth for lifted-part and wrong-height defects; without it
  the pipeline cannot score seating.
- A standard USD `extent` lets loaders and `BBoxCache` compute world bounds
  without traversing mesh points.
- Keeping the mm-valued `heightMm` separate from the render `extent` avoids
  unit ambiguity and keeps the defect ground truth explicit.

## Example

```usda
def Xform "U7"
{
    float pcba:component:heightMm = 1.0

    def Mesh "Body"
    {
        token pcba:mesh:role = "pkg_body"
        float3[] extent = [(-3.5, -3.5, 0), (3.5, 3.5, 1.0)]
    }
}
```

## How to comply

- Author `pcba:component:heightMm` in millimetres on every placed component.
- Author a correct USD `extent` on the body mesh so `BBoxCache` returns valid
  world bounds.
- Keep `heightMm` and `extent` consistent along Z.

### What the checker proves

`BodyHeightChecker` runs on electrical components only: it fails an absent `heightMm` (a
`pcba:prov:heightMm` marker downgrades this to a declared gap) and any authored value that is not
greater than zero. It does not check the body mesh `extent` or compare it with `heightMm`.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
