# Paste Association

| Code | BG.007 |
|------|------|
| Validator | `PasteAssociationChecker` |
| Applies to | `board_paste` prim (mesh role `board_paste`) |
| Requirement level | MUST when paste is supplied and the site is occupied (`refdes` + `componentPinNumber`); `pasteFor` rel SHOULD when the component prim exists |
| Tags | `board`, `paste`, `association` |

## Summary

When solder paste geometry is supplied, each `board_paste` deposit MUST name the contact it
serves with the same pair a pad or barrel uses: `pcba:board:refdes` +
`pcba:board:componentPinNumber`. The `pcba:board:pasteFor` relationship is a SHOULD — a direct
handle when the component prim is in the file — not the association itself.

This page follows PCBA to USD Input Contract **1.0.2**, sections 6 and 10.

## Description

Paste deposits are addressable `board_paste` prims, one per deposit — never one merged paste
mesh. Each deposit states which component contact it belongs to so the pipeline can attribute
paste volume to the right joint and drive paste-related defect classes.

**The association is the `refdes` + `componentPinNumber` pair, not the rel.** A refdes
survives stage restructuring and re-panelization where a prim path does not, and the pair is
authorable *before* the component prim exists — an exporter staging board copper ahead of
component geometry can state every association with the pair but could not emit a single rel.
Author `pcba:board:pasteFor` as well when the component prim is present; where both are
present they MUST agree, and the pair wins. The association is authored board-side, on the
non-instanced paste prim, so component prototypes stay instanceable.

The pair is owed when paste is supplied **and the site is occupied**. A no-stuff site is
pasted but has no contact; for paste **in a hole** (paste-in-hole,
[BG.014](/capabilities/pcb_aoi/board_geometry/requirements/paste-in-hole)) the barrel's
occupancy governs. For ordinary through-hole parts there is no paste and therefore no
association.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:board:refdes` | `string` | MUST when paste supplied and the site is occupied | The component whose contact this deposit serves. |
| `pcba:board:componentPinNumber` | `string` | as above | Which pin of that component; matches its `pcba:pin:number`. |
| `pcba:board:pasteFor` | `rel` | SHOULD, when the component prim exists | Direct handle to the component contact; must agree with the pair. Not the primary association. |
| `pcba:board:solderLayer` | `token` | MUST when paste supplied — or derivable | `top` \| `bottom` (BG.008). |

## Why is it required?

- Solder-joint synthesis needs to attribute each deposit to the correct contact.
- Paste-volume defect classes key off the deposit-to-contact link.
- A refdes-based pair is stable under restructuring and authorable before component
  geometry lands; a rel is neither.

## Example

```usda
def Mesh "paste_U7_1"
{
    token  pcba:mesh:role = "board_paste"
    token  pcba:mesh:matClass = "solder"
    token  pcba:board:solderLayer = "top"
    string pcba:board:refdes = "U7"
    string pcba:board:componentPinNumber = "1"
    rel    pcba:board:pasteFor = </Board/Layers/Top/Components/U7>   # SHOULD
}
```

## How to comply

- On every supplied `board_paste` deposit at an occupied site, author `pcba:board:refdes` and
  `pcba:board:componentPinNumber`.
- Add `pcba:board:pasteFor` when the component prim is in the file; keep it consistent with
  the pair.
- Author on the board-side paste prim, never on the instanced pin.
- Omit paste and its association for through-hole parts unless paste-in-hole applies (BG.014).

### What the checker proves

`PasteAssociationChecker` skips deposits carrying `pcba:board:occupied = false`. For every other
`board_paste` it fails when `pcba:board:refdes` is present without `componentPinNumber`, passes
when both are present, warns when only a `pasteFor` rel is authored (rel-only), treats a
`pcba:prov:refdes` / `pcba:prov:pasteFor` marker as a declared gap, and fails otherwise. Whether
the pair resolves to a real pin of the named component is checked by BG.012's resolution pass.
It does not verify that the rel target and the pair agree.

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Paste Side (BG.008)](/capabilities/pcb_aoi/board_geometry/requirements/paste-side)
- [Paste in Hole (BG.014)](/capabilities/pcb_aoi/board_geometry/requirements/paste-in-hole)
- [Hole Occupancy and Pin Association (BG.012)](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)
