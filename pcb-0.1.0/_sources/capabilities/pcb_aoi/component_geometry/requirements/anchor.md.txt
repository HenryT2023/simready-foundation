# Anchor & Geometry Reference

| Code | CG.002 |
|------|------|
| Validator | `AnchorChecker` |
| Applies to | `placed component prim` and its body `Mesh` |
| Requirement level | MUST (N/A for `fiducial` / `mechanical`) |
| Tags | `component`, `placement`, `anchor`, `geometry-reference` |

## Summary

The component asset root MUST sit at a declared anchor named by
`pcba:component:anchor` (`body_centroid`, `pin1`, `footprint_origin`, or
`mesh_origin`). `pcba:component:bodyCentroidLocal` and `pcba:mesh:originOffset`
together give deterministic placement when the mesh origin is off the body.

## Description

Placement values ([CG.001](/capabilities/pcb_aoi/component_geometry/requirements/placement))
are only meaningful relative to a known reference point on the component. The
`pcba:component:anchor` token declares which point the asset root — and therefore
`nominalPosMm` — refers to:

- `body_centroid` — the centroid of the component body.
- `pin1` — the pin-1 contact.
- `footprint_origin` — the land-pattern origin from the source footprint.
- `mesh_origin` — the origin of the source mesh as authored.

Because a source mesh origin is frequently **off the body** (e.g. at a datum in
the STEP model), two additional attributes make placement deterministic:
`pcba:component:bodyCentroidLocal` gives the body centroid in the component's
local frame, and `pcba:mesh:originOffset` gives the offset from the source mesh
origin to the anchor. With these, a consumer can compute the body position from
the anchored transform regardless of where the mesh origin happens to fall,
without inspecting geometry.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:anchor` | `token` | MUST | `body_centroid`, `pin1`, `footprint_origin`, `mesh_origin`; the asset root sits at this point |
| `pcba:component:bodyCentroidLocal` | `point3f` | MUST | Body centroid in the component-local frame |
| `pcba:mesh:originOffset` | `point3f` | MUST | On the component's `pkg_body` mesh: offset from the source mesh origin to the anchor |

## Why is it required?

- Placement (`nominalPosMm`) is ambiguous without knowing which point on the
  component it addresses; the anchor token removes that ambiguity.
- When the mesh origin is off-body, `bodyCentroidLocal` + `originOffset` let the
  pipeline seat the part deterministically without re-deriving geometry.
- A consistent anchor convention lets translate / rotate seat correctly across
  every component in the board.

## Example

```usda
def Xform "U7"
{
    token   pcba:component:anchor = "body_centroid"
    point3f pcba:component:bodyCentroidLocal = (0, 0, 0.45)

    def Mesh "Body"
    {
        token   pcba:mesh:role = "pkg_body"
        point3f pcba:mesh:originOffset = (-1.2, 0.6, 0)   # on the body mesh: source mesh origin -> anchor
    }
}
```

## How to comply

- Declare `pcba:component:anchor` on every placed component; make the asset root
  coincide with the named anchor point.
- Author `pcba:component:bodyCentroidLocal` and `pcba:mesh:originOffset` so the
  body position is computable even when the mesh origin is off-body.
- Keep the anchor convention consistent with the values in `nominalPosMm` /
  `nominalRotationDeg`.

### What the checker proves

`AnchorChecker` runs on electrical components only. It fails an absent `anchor` or one outside
the vocabulary, an absent `bodyCentroidLocal`, and a `pkg_body` mesh with no
`pcba:mesh:originOffset`; a matching `pcba:prov:` marker downgrades each to a declared gap. It does
not verify that the prim transform actually places the named anchor at `nominalPosMm`.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Placement (CG.001)](/capabilities/pcb_aoi/component_geometry/requirements/placement)
