# Hole and Pad Geometry

| Code | BG.010 |
|------|------|
| Validator | `HoleGeometryChecker` |
| Applies to | `board_barrel` prims (hole geometry); `board_pad` prims (pad contour) |
| Requirement level | MUST for hole geometry on `board_barrel` (derivable forms accepted); SHOULD for `padContour` |
| Tags | `board`, `hole`, `pad`, `geometry`, `tht` |

## Summary

Every `board_barrel` MUST describe its plated-through-hole geometry — `pcba:board:holeCenterMm`,
`pcba:board:holeShape`, `pcba:board:holeDimsMm` — **or** author one of the two derivable forms
the contract allows (a drill radius for a round hole; shape + dims + the contour mesh for a
slot). `pcba:board:padContour` on a `board_pad` is a SHOULD: the pad mesh itself is the
authoritative exposed-pad extent.

This page follows PCBA to USD Input Contract **1.0.2**, sections 6 and 10. The carrier of
hole data is the `board_barrel`, not `board_hole`; there is no `holeSide` attribute.

## Description

**Holes are real voids** through the substrate, not solid cylinders sitting on the board.
Filled vias / via-in-pad that are genuinely plated shut by design are real and are modelled as
manufactured. Each through-hole is described on its `board_barrel`
([BG.003](/capabilities/pcb_aoi/board_geometry/requirements/hole-plating)):

- `pcba:board:holeCenterMm` — the drill centre in board-local mm.
- `pcba:board:holeShape` — the bore shape token (e.g. `circular`, `slot`).
- `pcba:board:holeDimsMm` — the bore's axis-aligned bounds in mm (diameter, or major/minor).

Two **derivable forms** are conformant, on the principle that the contract asks for what an
exporter actually has:

1. A **round** hole MAY author only a drill radius — `pcba:board:holeRadiusMm` (`float`, the
   nominal tool size before plating). Centre, shape, and dims derive from it plus the prim
   transform. Author it on circular holes only; a radius quietly misrepresents a slot.
2. A **non-circular** hole (slot) MAY author `holeShape` + `holeDimsMm` with the full contour
   geometry and omit `holeCenterMm`; the centre derives from the geometry's extent.

`pcba:board:holeContour` (`point3f[]`) is an optional ROI-side refinement for a rotated or
irregular opening; the shape/dims pair is the authoring requirement.

**Pad extent is the exposed pad = the solder-mask opening**, not a per-pad copper contour — the
copper underneath is often a continuous pour, and the pad mesh MAY carry thickness. Because the
`board_pad` mesh already *is* the exposed pad, `pcba:board:padContour` is a **SHOULD** for both
SMT and THT: author it when the source has it, radius-only only for a circular pad. Where
per-pad geometry genuinely cannot be produced, defer with `pcba:prov:padContour`.

Applies to `through_hole` and `press_fit` alike; press-fit holes are still described here, and
whether solder-defect classes apply is determined per pin by `pcba:pin:solderable`.

## Fields

| Attribute | On | Type | Req | Notes |
|-----------|----|------|-----|-------|
| `pcba:board:holeCenterMm` | `board_barrel` | `float2` / `point3f` | MUST — or derivable | Drill centre, board-local mm. May be omitted when a radius form is authored, or when shape + dims + contour geometry are present. |
| `pcba:board:holeShape` | `board_barrel` | `token` | MUST — or derivable | Bore shape (e.g. `circular`, `slot`). Derivable from a radius form. |
| `pcba:board:holeDimsMm` | `board_barrel` | `float2` | MUST — or derivable | Axis-aligned bounds of the bore, mm. Derivable from a radius form. |
| `pcba:board:holeRadiusMm` | `board_barrel` | `float` | the circular alternative | Drill radius (nominal tool size). Circular holes only. |
| `pcba:board:holeContour` | `board_barrel` | `point3f[]` | OPTIONAL | ROI-side refinement for a rotated / irregular opening. |
| `pcba:board:padContour` | `board_pad` | `float2[]` / `point3f[]` | SHOULD (SMT and THT) | Outline of the exposed pad (mask opening). Optional where the pad mesh is itself authoritative. |

## Why is it required?

- Lead seating and the `hole_roi` need the true hole centre, shape, and bore.
- Accepting a bare drill radius or a contoured slot keeps the requirement satisfiable from the
  data fabrication exports actually contain.
- The exposed-pad mesh is what the camera sees; a separate contour is a restatement, so it is
  recommended rather than required.

## Example

```usda
# Full form
def Mesh "barrel_J1_1"
{
    token   pcba:mesh:role = "board_barrel"
    token   pcba:mesh:matClass = "copper"
    point3f pcba:board:holeCenterMm = (50.0, 10.0, 0.8)
    token   pcba:board:holeShape = "circular"
    float2  pcba:board:holeDimsMm = (1.0, 1.0)
    bool    pcba:board:occupied = true
    string  pcba:board:refdes = "J1"
    string  pcba:board:componentPinNumber = "1"
}

# Derivable form: drill radius only (circular hole)
def Mesh "barrel_J1_2"
{
    token   pcba:mesh:role = "board_barrel"
    token   pcba:mesh:matClass = "copper"
    float   pcba:board:holeRadiusMm = 0.5
    bool    pcba:board:occupied = true
    string  pcba:board:refdes = "J1"
    string  pcba:board:componentPinNumber = "2"
}

# Pad: the mesh is the exposed pad; padContour is an optional restatement
def Mesh "pad_J1_1"
{
    token pcba:mesh:role = "board_pad"
    token pcba:mesh:matClass = "copper"
    string pcba:board:padNumber = "1"
    point3f[] pcba:board:padContour = [(0,0,0),(1,0,0),(1,1,0),(0,1,0)]
    bool   pcba:board:occupied = true
    string pcba:board:refdes = "J1"
    string pcba:board:componentPinNumber = "1"
}
```

## How to comply

- On every `board_barrel`, author `holeCenterMm` + `holeShape` + `holeDimsMm`, or the drill
  radius for a round hole, or shape + dims + contour geometry for a slot.
- Do not author `pcba:board:holeSide`; do not put hole data on a `board_hole` prim expecting
  it to be read.
- Model each `board_pad` as the exposed pad (mask opening); add `padContour` when the source
  has it, radius-only for circular pads only.
- Keep everything in board-local mm.

### What the checker proves

`HoleGeometryChecker` inspects every `board_barrel`. If `pcba:board:holeRadiusMm` (or a
`pcba:board:holeDiameterMm` alternative) is authored it passes; otherwise it requires
`holeShape` and `holeDimsMm` to be declared, and `holeCenterMm` unless shape, dims, and a mesh
`extent` are all present. A `pcba:prov:<attr>` marker downgrades a missing field to a declared
gap. It does not check values, does not verify the hole is a real void, and does not check
`padContour` or the pad shape at all.

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Plated Barrel at Occupied Through-Hole Joints (BG.003)](/capabilities/pcb_aoi/board_geometry/requirements/hole-plating)
- [Pad Number (BG.005)](/capabilities/pcb_aoi/board_geometry/requirements/pad-number)
- [Hole Occupancy and Pin Association (BG.012)](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)
