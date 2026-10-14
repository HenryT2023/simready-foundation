# Origin Convention

| Code | UO.014 |
|------|------|
| Validator | `OriginConventionChecker` |
| Applies to | board-root prim (discovered by its `pcba:board:*` attributes) |
| Requirement level | MUST |
| Tags | `organization` |

## Summary

The board root MUST declare `pcba:board:originConvention` — how the board's zero was chosen:
`cad_bbox_lower_left`, `fiducial_f1`, `mounting_hole`, `datum_explicit`, or `unspecified`. When
it is `datum_explicit`, `pcba:board:originPointMm` MUST state where the datum is.
`pcba:board:originLabel` SHOULD name the datum feature.

This page follows PCBA to USD Input Contract **1.0.2**, section 11.

## Description

Board-local coordinates (`nominalPosMm`, hole centres, pad contours) are only meaningful
relative to a known origin. Real boards frequently put zero somewhere other than a corner — a
mounting hole is common, and the datum is sometimes **outside the board outline** entirely.
State it rather than letting a consumer assume a corner.

- `cad_bbox_lower_left` — lower-left of the CAD bounding box.
- `fiducial_f1` — the primary fiducial.
- `mounting_hole` — a mounting hole.
- `datum_explicit` — an explicitly stated datum; `originPointMm` is then required.
- `unspecified` — not declared / not known.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:board:originConvention` | `token` | MUST | `cad_bbox_lower_left \| fiducial_f1 \| mounting_hole \| datum_explicit \| unspecified`. |
| `pcba:board:originPointMm` | `float2` | MUST when `originConvention = datum_explicit` | The datum in board-local mm; may lie outside the outline. |
| `pcba:board:originLabel` | `string` | SHOULD | Human / CAD name of the datum feature, e.g. `MH1`, `A1-datum`. |

## Why is it required?

- Every board-local coordinate depends on a known origin; without a declared convention the
  numbers are ambiguous.
- Stating the datum explicitly removes the corner assumption that mis-places every component
  on boards anchored to a mounting hole.

## Example

```usda
def Xform "Board"
{
    token  pcba:board:originConvention = "datum_explicit"
    float2 pcba:board:originPointMm = (5.0, 5.0)    # MUST when datum_explicit
    string pcba:board:originLabel = "MH1"
}
```

## How to comply

- Author `pcba:board:originConvention` on the board root with the token that matches the
  source's zero.
- For `datum_explicit`, author `originPointMm`; add `originLabel` wherever the datum has a name.
- Use `unspecified` only when the convention genuinely cannot be determined; a pending value
  may be deferred with `pcba:prov:originConvention`.

### What the checker proves

`OriginConventionChecker` fails when the board root lacks `originConvention` (a
`pcba:prov:originConvention` marker downgrades this to a declared gap), when its value is
outside the vocabulary, and when `datum_explicit` is declared without `originPointMm`. It does
not check `originLabel` or verify the stated datum against the geometry.

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Board Root (UO.001)](/capabilities/pcb_aoi/usd_organization/requirements/board-root)
