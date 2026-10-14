# Plated Barrel at Occupied Through-Hole Joints

| Code | BG.003 |
|------|------|
| Validator | `PlatedBarrelChecker` |
| Applies to | `board_barrel` meshes; every placed through-hole / press-fit component |
| Requirement level | MUST (for every plated hole at an occupied through-hole joint, `press_fit` included) |
| Tags | `board`, `geometry`, `tht` |

## Summary

Every plated hole at an **occupied through-hole joint** MUST be backed by a `Mesh` with
`pcba:mesh:role = "board_barrel"` — the copper plating through the board thickness. This
includes `press_fit` parts. The barrel carries the hole data and the board-side association
(`pcba:board:refdes` + `pcba:board:componentPinNumber`) for that joint.

This page follows PCBA to USD Input Contract **1.0.2**, sections 6 and 10.
There is no `pcba:board:plated` flag; `board_hole` prims are optional bookkeeping.

## Description

**The barrel is the hole.** A `board_barrel` is both the required geometry (the copper tube
the camera looks down) and the prim that carries the drill facts (`holeCenterMm` /
`holeShape` / `holeDimsMm` or a drill radius — see
[Hole and Pad Geometry (BG.010)](/capabilities/pcb_aoi/board_geometry/requirements/hole-and-pad-geometry)),
`pcba:board:occupied`, and the association pair when occupied
([BG.012](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)).

The requirement is scoped to joints the pipeline inspects:

- **Barrel required:** every plated hole in which a through-hole terminal sits — `processClass`
  `through_hole` **or** `press_fit`. A press-fit part is a solderless through-hole part: the hole
  is plated, the barrel is real, and the camera looks down it. Whether *solder-defect classes*
  apply there is determined separately, per pin, by `pcba:pin:solderable`.
- **No barrel required:** a plated via with no component in it, and any unplated hole (a bare
  drilled mounting hole). Neither forms a solder joint. Unplated holes carry no required
  attributes at all; where a screw or standoff sits in one, the `mechanical` placement describes
  it.

Two attributes are deliberately not part of the contract and are silently ignored when present:
`pcba:board:plated` (a barrel *is* the plating, so a flag would only restate its own presence) and
`pcba:board:holeSide` (a through-hole goes all the way through). An exporter that
boolean-subtracts real voids should tag the copper annular tube `board_barrel`; tagging it
`board_hole` is the common mistake.

A through-hole joint is therefore three prims — component-side annular ring (`board_pad`),
solder-side annular ring (`board_pad`), and the barrel — all carrying the same
`pcba:board:refdes` + `pcba:board:componentPinNumber`.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:mesh:role` | `token` | MUST | `"board_barrel"` on the plating of every occupied through-hole joint (incl. `press_fit`). |
| `pcba:board:refdes` | `string` | MUST when occupied | The component whose terminal sits in this hole (BG.012). |
| `pcba:board:componentPinNumber` | `string` | MUST when occupied | Which pin of that component; matches its `pcba:pin:number` (BG.012). |
| `pcba:board:occupied` | `bool` | MUST | Is a terminal in this hole (BG.012). |
| `pcba:board:holeCenterMm` · `holeShape` · `holeDimsMm` / `holeRadiusMm` | see BG.010 | MUST — or derivable | Drill geometry, carried on the barrel (BG.010). |

## Why is it required?

- The barrel is the through-hole copper the AOI camera sees; without it there is no
  through-hole joint to render or inspect.
- It is the one prim guaranteed to exist wherever a THT joint exists, so it is the reliable
  home for the hole data and the association.
- Scoping the requirement to occupied joints avoids authoring thousands of barrels for vias
  that are never inspected.

## Example

```usda
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
    rel     pcba:board:component = </Board/THT/J1>     # SHOULD; must agree with refdes
}

# Unplated mounting hole: no barrel, no required attributes. An optional board_hole
# bookkeeping prim is permitted but nothing downstream reads it.
```

## How to comply

- For every pin of every `through_hole` or `press_fit` component, author one `board_barrel`
  mesh carrying that joint's `pcba:board:refdes` + `pcba:board:componentPinNumber`, its
  `occupied` state, and the hole geometry (BG.010).
- Barrels are optional for unoccupied plated vias; unplated holes have no plating
  to represent. Do not author `pcba:board:plated` or `pcba:board:holeSide`.
- Tag the plated copper tube `board_barrel`, not `board_hole`.

### What the checker proves

`PlatedBarrelChecker` runs only when a `through_hole` or `press_fit` component is placed. It
collects that component's **joints** — pins that are solderable, or press-fit (terminal form
`pressFit`, or the part's process class is `press_fit`) — and fails each joint for which no
`board_barrel` carries the matching `pcba:board:refdes` + `pcba:board:componentPinNumber`; a
stage with no barrel geometry at all is reported once. A non-solderable pin that is not press-fit
(a locating peg, a mechanical lead in an unplated hole) forms no joint and owes no barrel; such
features are better modelled as package body geometry than as pins. The checker does not verify
that the barrel is a real void through the substrate, that its geometry sits at the pin, or that
its `occupied` flag is set — those are BG.010 / BG.012 and manual inspection.

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Hole and Pad Geometry (BG.010)](/capabilities/pcb_aoi/board_geometry/requirements/hole-and-pad-geometry)
- [Hole Occupancy and Pin Association (BG.012)](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)
