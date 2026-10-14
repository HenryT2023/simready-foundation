# Requirements

## Summary

Levels follow PCBA to USD Input Contract **1.0.2**.

- The board root **MUST** carry `pcba:board:thicknessMm` — the pressed board thickness — and `board_substrate` **MUST** be a solid slab of that thickness (BG.001)
- The board **MUST** carry copper-layer geometry (`board_copper`) and solder-mask geometry (`board_mask`) with role-consistent materials (BG.002)
- Every plated hole at an **occupied** through-hole joint, `press_fit` included, **MUST** be backed by a `board_barrel` that carries the hole data and the association pair; there is no `pcba:board:plated` flag and `board_hole` is optional bookkeeping (BG.003)
- Each `board_pad` **MUST** carry `pcba:board:padNumber`, its designation within the footprint, present even on an unoccupied pad; on an occupied pad it should equal `componentPinNumber` (BG.005)
- When solder paste is supplied, each `board_paste` at an occupied site **MUST** name its contact with `pcba:board:refdes` + `pcba:board:componentPinNumber` (`pcba:board:pasteFor` is a SHOULD handle) (BG.007), and its side **MUST** be determinable — `pcba:board:solderLayer` or a containing layer's `pcba:layer:side` (BG.008)
- Each `board_barrel` **MUST** describe its hole — `holeCenterMm` / `holeShape` / `holeDimsMm`, or a drill radius for a round hole, or shape + dims + contour for a slot; `pcba:board:padContour` is a **SHOULD**, the pad mesh being the authoritative exposed-pad extent (BG.010)
- `board_pad` and `board_barrel` prims **MUST** declare occupancy (or an explicit unresolved-occupancy marker); occupied sites carry `pcba:board:refdes` + `pcba:board:componentPinNumber` **board-side**, keeping component pins instanceable. Known-empty pads also declare `intentionallyUnpopulated` (BG.012)
- For THT, paste association **MUST** be empty unless paste-in-hole applies (BG.014; no executable rule)

## Requirements

```{requirements-table}
```

```{toctree}
:maxdepth: 1
:hidden:

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
