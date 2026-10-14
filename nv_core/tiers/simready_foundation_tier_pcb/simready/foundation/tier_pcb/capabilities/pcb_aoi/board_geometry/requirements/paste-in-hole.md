# Paste in Hole

| Code | BG.014 |
|------|------|
| Validator | _Not yet implemented_ |
| Applies to | `board_paste` / `board_barrel` prims (THT) |
| Requirement level | MUST when paste-in-hole applies (otherwise no paste association for THT) |
| Tags | `board`, `paste`, `hole`, `tht` |

## Summary

For through-hole components the paste association MUST be **empty** unless the paste-in-hole
(pin-in-paste / through-hole reflow) process applies. When it does, the deposit is a normal
`board_paste` prim naming its contact with `pcba:board:refdes` + `pcba:board:componentPinNumber`
and carrying its side, exactly like SMT paste.

This page follows PCBA to USD Input Contract **1.0.2**, sections 10 and 12.

## Description

Standard through-hole parts are wave- or selective-soldered and have **no solder paste**, so no
`board_paste` deposit and no association exist for their holes. Authoring an empty or fabricated
paste association for an ordinary through-hole joint would mislead solder synthesis.

The exception is **paste-in-hole**, where paste is stencil-printed over or into the plated hole
so the lead reflows with the SMT parts. In that case the board supplies a `board_paste` deposit
for the hole and it MUST carry the normal association
([BG.007](/capabilities/pcb_aoi/board_geometry/requirements/paste-association)) and side
([BG.008](/capabilities/pcb_aoi/board_geometry/requirements/paste-side)). For paste in a hole the
**barrel's** occupancy governs whether the pair is owed.

This requirement is a conditional gate keyed on the actual assembly process, not on
`processClass` alone. Whether a given pin takes solder at all is stated per pin by
`pcba:pin:solderable`.

## Fields

| Attribute | On | Type | Req | Notes |
|-----------|----|------|-----|-------|
| `pcba:board:refdes` · `pcba:board:componentPinNumber` | `board_paste` | `string` | MUST when paste-in-hole (else no deposit exists for the THT joint) | The through-hole contact the deposit serves (BG.007). |
| `pcba:board:solderLayer` | `board_paste` | `token` | MUST when paste-in-hole — or derivable | `top` \| `bottom` (BG.008). |
| `pcba:board:pasteFor` | `board_paste` | `rel` | SHOULD when the component prim exists | Direct handle; must agree with the pair. |

## Why is it required?

- Ordinary THT has no paste; a spurious association would inject false paste geometry and
  defects.
- Paste-in-hole is a real reflow process that does deposit paste on the hole and must be
  modelled like SMT paste.

## Example

```usda
# Ordinary through-hole joint: barrel only, NO board_paste.
def Mesh "barrel_J1_1"
{
    token  pcba:mesh:role = "board_barrel"
    token  pcba:mesh:matClass = "copper"
    float  pcba:board:holeRadiusMm = 0.5
    bool   pcba:board:occupied = true
    string pcba:board:refdes = "J1"
    string pcba:board:componentPinNumber = "1"
}

# Paste-in-hole process: a board_paste deposit IS supplied and associated.
def Mesh "paste_J2_1"
{
    token  pcba:mesh:role = "board_paste"
    token  pcba:mesh:matClass = "solder"
    token  pcba:board:solderLayer = "top"
    string pcba:board:refdes = "J2"
    string pcba:board:componentPinNumber = "1"
}
```

## How to comply

- For wave- or selective-soldered THT, author no `board_paste` for the joint.
- For paste-in-hole parts, author a `board_paste` deposit with the `refdes` +
  `componentPinNumber` pair and its side, as for SMT paste.
- Gate on the actual assembly process.

No executable rule exists for this code; it is not part of the enforced feature set.

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Paste Association (BG.007)](/capabilities/pcb_aoi/board_geometry/requirements/paste-association)
- [Paste Side (BG.008)](/capabilities/pcb_aoi/board_geometry/requirements/paste-side)
