# Pad Number

| Code | BG.005 |
|------|------|
| Validator | `PadNumberChecker` |
| Applies to | `board_pad` prim (mesh role `board_pad`) |
| Requirement level | MUST |
| Tags | `board`, `pad`, `association` |

## Summary

Every `board_pad` prim MUST carry `pcba:board:padNumber` — the pad's own designation within its
footprint — present **even on an unoccupied pad**. On an occupied pad it should equal that
pad's `pcba:board:componentPinNumber`.

This page follows PCBA to USD Input Contract **1.0.2**, sections 6 and 10.

## Description

A `board_pad` is the component solder-attachment copper: the land for an SMT terminal, the
annular ring for a THT terminal — one pad per physical joint, per side. `pcba:board:padNumber`
is a board-side label: the pad's designation within its footprint, stable within that footprint
but not board-unique. Board-wide identity is `pcba:board:refdes` + `padNumber`.

It is distinct from the association. The association to a component pin is the
`pcba:board:refdes` + `pcba:board:componentPinNumber` pair
([BG.012](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)); `padNumber` is
present regardless of occupancy, so a no-stuff pad carries a `padNumber` but no `refdes`. On an
occupied pad the two numbers should agree — a mismatch is a cross-check that catches a wrong
footprint or rotation.

This presupposes per-pad addressable geometry: one `board_pad` prim per contact, with pad
extent equal to the solder-mask opening (the copper underneath may remain a single pour). CAD
flashes contributing to the same attachment site are merged into one logical pad *where the
contact resolves*; unresolved flashes stay separate and defer their association. Where per-pad
geometry genuinely cannot be produced, declare the gap with `pcba:prov:padNumber` rather than
inventing a number.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:board:padNumber` | `string` | MUST | The pad's designation within its footprint; present even when `occupied = false`. Should equal `componentPinNumber` on an occupied pad. |

## Why is it required?

- A pad must be addressable on its own, whether or not a part is fitted — a no-stuff site is
  still a real pad the AOI camera sees.
- Agreement between `padNumber` and `componentPinNumber` is a cheap cross-check on footprint
  and rotation.
- Board-side authoring keeps component prototypes shareable and instanceable.

## Example

```usda
def Mesh "pad_U7_1"
{
    token  pcba:mesh:role = "board_pad"
    token  pcba:mesh:matClass = "copper"
    string pcba:board:padNumber = "1"
    bool   pcba:board:occupied = true
    string pcba:board:refdes = "U7"
    string pcba:board:componentPinNumber = "1"   # equals padNumber on an occupied pad
}

def Mesh "pad_R99_1"
{
    token  pcba:mesh:role = "board_pad"
    token  pcba:mesh:matClass = "copper"
    string pcba:board:padNumber = "1"            # present even though unoccupied
    bool   pcba:board:occupied = false
    bool   pcba:board:intentionallyUnpopulated = true
}
```

## How to comply

- Author one `board_pad` prim per component contact per side, with extent equal to the mask
  opening.
- Author `pcba:board:padNumber` on every pad, occupied or not, as a string.
- On occupied pads keep it equal to `pcba:board:componentPinNumber`.

### What the checker proves

`PadNumberChecker` fails a `board_pad` whose `pcba:board:padNumber` is absent (unless a
`pcba:prov:padNumber` marker declares the gap) or declared but empty. It does not compare
`padNumber` with `componentPinNumber` or with any `pcba:pin:number`, and it does not check that
the copper has been segmented into one pad per contact.

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Hole and Pad Geometry (BG.010)](/capabilities/pcb_aoi/board_geometry/requirements/hole-and-pad-geometry)
- [Hole Occupancy and Pin Association (BG.012)](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)
