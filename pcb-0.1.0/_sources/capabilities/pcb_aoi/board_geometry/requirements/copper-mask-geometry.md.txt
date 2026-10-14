# Copper and Solder-Mask Geometry

| Code | BG.002 |
|------|------|
| Validator | `BoardLayersChecker` |
| Applies to | Board layer geometry (`board_copper`, `board_mask` meshes) |
| Requirement level | MUST |
| Tags | `board`, `geometry`, `appearance` |

## Summary

The board MUST carry copper-layer geometry and solder-mask geometry with role-consistent
materials: at least one `Mesh` with `pcba:mesh:role = "board_copper"` and at least one with
`pcba:mesh:role = "board_mask"`, so the rendered board has production-accurate colour and finish.

This page follows PCBA to USD Input Contract **1.0.2**, sections 5 and 9.

## Description

AOI reasons over the board's visible conductive and masked surfaces: exposed copper (traces,
pours, test points) and the solder-mask coat that gives the board its colour. Both are MUST.
Without copper there is no conductor to inspect against; without mask the rendered colour and
the copper/mask boundaries — a primary AOI signal — are unavailable.

Copper and mask are their own role-tagged meshes, not inferred from the substrate. The stackup
must be coherent: top-side copper/mask/paste sit above the top face, bottom-side layers below
the bottom face, and layers do not interpenetrate. Top, inner, and bottom are all layers; only
the inner layers are optional for AOI.

Keep roles honest. Silkscreen is `board_silk`, fiducial marks are `board_fiducial`, test points
are `board_testpoint`, and component attachment lands are `board_pad`; none of them are
`board_copper`. Each mesh's bound material must agree with its role by class
([UO.017](/capabilities/pcb_aoi/usd_organization/requirements/role-material)); `matClass`
derives from the role for board meshes and need not be authored.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:mesh:role` | `token` | MUST | `"board_copper"` on copper-layer meshes; `"board_mask"` on solder-mask meshes. At least one of each MUST exist. |

## Why is it required?

- Exposed copper is the conductor AOI inspects; it must exist as inspectable geometry.
- Solder mask defines the board's rendered colour/finish and the copper/mask boundaries AOI
  keys on.
- Separate role-tagged layers let the pipeline render and inspect them independently.

## Example

```usda
def Mesh "TopCopper"
{
    token pcba:mesh:role = "board_copper"
    token pcba:mesh:matClass = "copper"       # optional: derives from the role
}
def Mesh "TopMask"
{
    token pcba:mesh:role = "board_mask"
    token pcba:mesh:matClass = "mask"
}
```

## How to comply

- Author copper-layer geometry as one or more `board_copper` meshes and solder-mask geometry
  as one or more `board_mask` meshes, per side, above/below the substrate faces.
- Bind materials of the matching class (UO.017); do not fold silkscreen, fiducials, test
  points, or pads into `board_copper`.

### What the checker proves

`BoardLayersChecker` fails when no mesh on the stage carries role `board_copper`, and when none
carries `board_mask`. It does not check layer placement, interpenetration, or material
accuracy; role/material agreement is UO.017.

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Mesh Role (UO.009)](/capabilities/pcb_aoi/usd_organization/requirements/mesh-role)
