# Hole Occupancy and Pin Association

| Code | BG.012 |
|------|------|
| Validator | `HoleOccupancyChecker` |
| Compatibility | {compatibility}`open-usd` |
| Applies to | `board_pad` and `board_barrel`; association resolution also covers `board_paste` |
| Requirement level | MUST, conditional on site occupancy |
| Tags | `board`, `pad`, `barrel`, `association`, `instanceable` |

## Summary

Every `board_pad` and `board_barrel` MUST declare `pcba:board:occupied`, or declare
that occupancy is unresolved using the provenance convention below. An occupied
site names its component terminal with **`pcba:board:refdes` +
`pcba:board:componentPinNumber`**. This applies to SMT pads as well as THT joints.

This page follows PCBA to USD Input Contract **1.0.2**, sections 6 and 10.
`board_hole` is optional bookkeeping; occupancy and association belong on the
actual pad or barrel. There are no `holeSide` or `plated` fields.

## Description

Author associations board-side so component pins can remain in shared,
instanceable package prototypes. The pair resolves within the containing board;
repeated panel positions resolve within their own board, not across the panel.
`componentPinNumber` matches the component's `pcba:pin:number` and is distinct
from the pad's own `pcba:board:padNumber`.

When the component prim exists, `pcba:board:component` is a SHOULD relationship
to it. Its absence is not a failure; when authored it must agree with `refdes`.
The pair is authoritative. A bare board-side `pcba:pin:number` is also read, with
a warning; author `pcba:board:componentPinNumber`.

A THT joint has a top ring, solder-side ring, and barrel, all carrying the same
association. At most one pad per side and one barrel may claim a given terminal.
A pad that names one pin but sits on another pin of that component is incorrect.

### Known empty versus unresolved

- On a pad with `occupied = false`, author `intentionallyUnpopulated`: `true`
  means no-stuff by design; `false` means a genuinely missing component.
- An unoccupied barrel does not require `intentionallyUnpopulated`.
- If occupancy is unresolved, **omit `occupied`** and author
  `string pcba:prov:occupied = "not_yet_available"` (or `"source_data_required"`
  after unsuccessful sourcing). Do not author `intentionallyUnpopulated` while
  occupancy is unresolved. Neither an association nor a no-stuff claim is owed
  for an unresolved site. The checker emits an INFO declared gap.

## Fields

| Attribute | Type | Requirement |
|-----------|------|-------------|
| `pcba:board:occupied` | `bool` | MUST on pads and barrels, unless explicitly deferred |
| `pcba:board:intentionallyUnpopulated` | `bool` | MUST on pads with authored `occupied = false` |
| `pcba:board:refdes` | `string` | MUST when occupied |
| `pcba:board:componentPinNumber` | `string` | MUST when occupied; references a component pin |
| `pcba:board:component` | relationship | SHOULD when occupied and the component prim exists |

## Why is it required?

Solder generation and joint inspection need the correct terminal at each site.
Explicit occupancy distinguishes a designed no-stuff site from a missing part,
and explicit deferral avoids inventing either condition when the data is unknown.

## Examples

These fragments illustrate metadata; geometry and other required fields are omitted.

```usda
def Mesh "Pad_J1_1"
{
    custom token pcba:mesh:role = "board_pad"
    custom string pcba:board:padNumber = "1"
    custom bool pcba:board:occupied = true
    custom string pcba:board:refdes = "J1"
    custom string pcba:board:componentPinNumber = "1"
    rel pcba:board:component = </Board/Components/J1>
}

def Mesh "Pad_NoStuff"
{
    custom token pcba:mesh:role = "board_pad"
    custom string pcba:board:padNumber = "2"
    custom bool pcba:board:occupied = false
    custom bool pcba:board:intentionallyUnpopulated = true
}

def Mesh "Pad_Unresolved"
{
    custom token pcba:mesh:role = "board_pad"
    custom string pcba:board:padNumber = "3"
    custom string pcba:prov:occupied = "not_yet_available"
}
```

## How to comply

Author occupancy and the conditional fields on each actual board site. Preserve
the board-side association when composing component prototypes. Verify that pin
numbers resolve, that THT rings and barrels name the same terminal, and that pad
positions agree with the claimed pins.

The checker uses available component geometry and layer-side metadata for its
cross-checks. It cannot verify an unresolved component or a geometric association
without geometry evidence. The pad-sits-at-its-pin check applies to surface-mount
parts only: a through-hole lead is a bent or long mesh whose extent centroid does not
mark where it enters the board, so a through-hole joint's location is established by
its barrel (BG.003, BG.010) rather than by this check. A pad whose footprint overlaps its
named pin's footprint is at that pin even when another pin lies nearer its centre, as with
connector pins that share one land. Read the reporting limits in the
[PCB-Assembly guide](/profiles/pcb_assembly).

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Hole and Pad Geometry (BG.010)](/capabilities/pcb_aoi/board_geometry/requirements/hole-and-pad-geometry)
