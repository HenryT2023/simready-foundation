# Pin-1 Position

| Code | CG.008 |
|------|------|
| Validator | `Pin1PositionChecker` |
| Applies to | `placed component prim` |
| Requirement level | CONDITIONAL — keyed / orientation-sensitive parts (N/A for `fiducial` / `mechanical`) |
| Tags | `component`, `pins`, `orientation`, `ground-truth` |

## Summary

`pcba:component:pin1PosMm` (a `point3f`) gives the actual offset of pin 1 from the
component anchor. It is required for keyed or orientation-sensitive parts and is
the ground truth for pin-1 orientation defects.

## Description

For a part where orientation matters — a keyed connector, a polarized IC, any
package with a pin-1 datum — the pipeline needs the **actual** pin-1 location to
inject and score orientation defects (part rotated 90°/180°, pin-1 in the wrong
corner). `pcba:component:pin1PosMm` gives that location as an offset from the
declared anchor
([CG.002](/capabilities/pcb_aoi/component_geometry/requirements/anchor)), in
millimetres.

The value MUST be the true measured offset, **not assumed** to sit at a package
corner: many packages place pin 1 inset from the corner or along an edge, and a
corner assumption produces wrong orientation ground truth. The field is
conditional — it MUST be authored when the part is keyed or orientation-sensitive
and MAY be omitted for a symmetric part where pin 1 is not orientation-bearing.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:pin1PosMm` | `point3f` | MUST when keyed / orientation-sensitive | Actual offset of pin 1 from the anchor, in mm; not assumed at a corner |

## Why is it required?

- Pin-1 location is the ground truth for orientation defects; without it the
  pipeline cannot tell a correctly oriented part from a rotated one.
- Requiring the measured offset (not a corner assumption) keeps the orientation
  ground truth correct for packages with inset or edge pin-1 datums.

## Example

```usda
def Xform "J3"
{
    token pcba:component:anchor = "body_centroid"
    point3f pcba:component:pin1PosMm = (-2.75, 1.27, 0)
}
```

## How to comply

- Author `pcba:component:pin1PosMm` for every keyed or orientation-sensitive part.
- Use the true measured offset from the anchor; do not assume pin 1 is at a
  corner.
- Omit it only for symmetric parts where pin 1 carries no orientation meaning.

### What the checker proves

`Pin1PositionChecker` is advisory because "keyed" is not reliably detectable: it warns when a part
declares `polarityType` or has `pinCount` greater than 2 and carries no `pin1PosMm`. It never
fails, and it does not verify the offset against the pin-1 geometry.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Anchor & Geometry Reference (CG.002)](/capabilities/pcb_aoi/component_geometry/requirements/anchor)
- [Polarity (CG.009)](/capabilities/pcb_aoi/component_geometry/requirements/polarity)
