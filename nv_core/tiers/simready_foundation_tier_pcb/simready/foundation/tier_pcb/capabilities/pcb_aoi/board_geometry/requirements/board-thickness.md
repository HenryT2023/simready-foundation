# Board Thickness

| Code | BG.001 |
|------|------|
| Validator | `BoardThicknessChecker` |
| Applies to | board-root prim (discovered by its `pcba:board:*` attributes) |
| Requirement level | MUST |
| Tags | `board`, `geometry`, `stackup` |

## Summary

The board-root prim MUST carry `pcba:board:thicknessMm`, the real **pressed** (post-lamination)
board thickness in millimetres, and the `board_substrate` mesh MUST be a solid slab of that
thickness — a zero-thickness plane is invalid.

This page follows PCBA to USD Input Contract **1.0.2**, sections 5 and 11.

## Description

Board thickness is the finished, pressed thickness of the bare board along the board normal
(Z, per the mm / Z-up stage conventions) — the post-lamination value, not the sum of input
material thicknesses. It is a single scalar authored once on the board root: the prim that
carries the `pcba:board:*` metadata. That prim MAY be the default prim but need not be; it is
found by attribute, not by name or position.

The pipeline uses it to seat through-hole leads (the barrel spans the substrate), to place
solder-side geometry relative to the component side, and to reason about the board's Z extent
independently of any substrate mesh bounds. It is a MUST for every board regardless of
`processClass`. The substrate itself (`board_substrate`) must be a solid slab with real
thickness so it has top and bottom faces and something for holes to pass through.

If the value is not yet available, omit it and author
`string pcba:prov:thicknessMm = "not_yet_available"` on the board root — the marker uses the
bare leaf name.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:board:thicknessMm` | `float` | MUST | Pressed board thickness along Z, mm; authored on the board-root prim. |

## Why is it required?

- Through-hole lead seating and barrel geometry depend on the substrate thickness the lead
  passes through.
- Solder-side generation needs the top-to-bottom span.
- A single authored scalar removes any dependence on imported mesh bounds that may include
  mask or silkscreen.

## Example

```usda
def Xform "Board"
{
    string pcba:board:generatorVersion = "example_pcb_export 1.4.2"
    string pcba:board:contentHash = "sha256:0000…"
    float  pcba:board:thicknessMm = 1.6        # pressed thickness, not input stackup sum
    token  pcba:board:originConvention = "cad_bbox_lower_left"

    def Mesh "Substrate"
    {
        token pcba:mesh:role = "board_substrate"
        float3[] extent = [(0, 0, 0), (80, 60, 1.6)]
    }
}
```

## How to comply

- Author `pcba:board:thicknessMm` on the board-root prim as a single float in mm.
- Use the finished pressed thickness from fabrication data; do not derive it from mesh bounds.
- Model `board_substrate` as a solid slab of that thickness.
- If the value is pending, omit it and author `pcba:prov:thicknessMm = "not_yet_available"`.

### What the checker proves

`BoardThicknessChecker` locates the board root by its `pcba:board:*` attributes and fails when
`pcba:board:thicknessMm` is absent or its value is not greater than zero. It does not
honour a `pcba:prov:thicknessMm` marker (an absent value fails even when deferred), and it does
not check that the substrate mesh is a solid slab of that thickness.

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Board Root (UO.001)](/capabilities/pcb_aoi/usd_organization/requirements/board-root)
