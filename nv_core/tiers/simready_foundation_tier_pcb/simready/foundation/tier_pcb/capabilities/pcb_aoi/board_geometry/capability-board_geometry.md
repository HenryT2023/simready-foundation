# PCB Board Geometry

## Overview

This capability defines the **board-level geometry (BG)** an exporter authors on the board USD
so a PCB AOI synthetic-data pipeline can generate solder joints and reason about through-hole
seating. It covers the fab-derived substrate, copper, mask, pad, paste, and plated-barrel
geometry that lives on the board (mesh roles `board_substrate`, `board_copper`, `board_mask`,
`board_pad`, `board_paste`, `board_barrel`; `board_hole` is optional bookkeeping) together with
the **board-side associations** that link those features to placed components and their pins.

The board is the source of truth for *source geometry and associations only*. The pipeline
consumes these to synthesize the downstream-generated solder-joint geometry and per-joint AOI
ROIs, which are out of scope for the authored asset. There is no `board_solder` role: solder is
generated, not exported.

Two rules shape every page here (PCBA to USD Input Contract **1.0.2**, sections 3, 6, 10):

- **Geometry breakout.** Every independently inspectable thing is its own addressable prim —
  each pad / annular ring, each barrel, each paste deposit. A merged copper or paste mesh cannot
  be defected or associated.
- **Associations are authored board-side, as the `pcba:board:refdes` +
  `pcba:board:componentPinNumber` pair.** The pair lives on the non-instanced `board_pad`,
  `board_barrel`, and `board_paste` prims, never on the instanced pin prim, so components stay
  `instanceable`. `pcba:board:component` / `pcba:board:pasteFor` rels are SHOULD direct handles,
  not the association. See
  [Hole Occupancy and Pin Association (BG.012)](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy).

SMT and THT are one model with conditional fields keyed off `pcba:component:processClass`: SMT
contributes paste deposits (pair + `solderLayer`) and per-contact pads; THT contributes a
`board_barrel` at every occupied joint (`press_fit` included) carrying the hole data and the
pair. `pcba:board:occupied` applies to both. `pcba:board:plated` and `pcba:board:holeSide` are
not contract attributes and are ignored when present; a bare board-side `pcba:pin:number` is read
with a warning, never required. This capability realizes the **Board-level Geometry (BG)** codes
BG.001–BG.014; BG.013 is intentionally unassigned and BG.014 has no executable rule.

## Requirements

| Code | Requirement | Summary |
|------|-------------|---------|
| BG.001 | [Board Thickness](/capabilities/pcb_aoi/board_geometry/requirements/board-thickness) | The board root MUST carry `pcba:board:thicknessMm` (pressed thickness) and the substrate MUST be a solid slab. |
| BG.002 | [Copper and Solder-Mask Geometry](/capabilities/pcb_aoi/board_geometry/requirements/copper-mask-geometry) | At least one `board_copper` and one `board_mask` mesh MUST exist, with role-consistent materials. |
| BG.003 | [Plated Barrel at Occupied Through-Hole Joints](/capabilities/pcb_aoi/board_geometry/requirements/hole-plating) | Every plated hole at an occupied THT joint (incl. `press_fit`) MUST have a `board_barrel` carrying the hole data and the association pair; there is no `plated` flag. |
| BG.005 | [Pad Number](/capabilities/pcb_aoi/board_geometry/requirements/pad-number) | Each `board_pad` MUST carry `pcba:board:padNumber` (its footprint designation), present even when unoccupied. |
| BG.007 | [Paste Association](/capabilities/pcb_aoi/board_geometry/requirements/paste-association) | Each supplied `board_paste` at an occupied site MUST name its contact with `refdes` + `componentPinNumber`; `pasteFor` rel is SHOULD. |
| BG.008 | [Paste Side](/capabilities/pcb_aoi/board_geometry/requirements/paste-side) | Each `board_paste` side MUST be determinable: `pcba:board:solderLayer` or a containing layer's `pcba:layer:side`. |
| BG.010 | [Hole and Pad Geometry](/capabilities/pcb_aoi/board_geometry/requirements/hole-and-pad-geometry) | `board_barrel` MUST carry centre/shape/dims or a derivable form (drill radius; slot shape + dims + contour); `padContour` is SHOULD. |
| BG.012 | [Hole Occupancy and Pin Association](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy) | Pads and barrels declare occupancy or its unresolved marker; occupied sites name `refdes` + `componentPinNumber` board-side. Known-empty pads also declare the no-stuff state. |
| BG.014 | [Paste in Hole](/capabilities/pcb_aoi/board_geometry/requirements/paste-in-hole) | For THT, paste association MUST be empty unless paste-in-hole applies. No executable rule. |

```{toctree}
:maxdepth: 1
:hidden:

requirements
requirements/board-thickness
requirements/copper-mask-geometry
requirements/hole-plating
requirements/pad-number
requirements/paste-association
requirements/paste-side
requirements/hole-and-pad-geometry
requirements/hole-occupancy
requirements/paste-in-hole
```
