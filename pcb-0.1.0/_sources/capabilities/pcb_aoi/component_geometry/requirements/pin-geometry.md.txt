# Pin Geometry

| Code | CG.007 |
|------|------|
| Validator | `PinGeometryChecker` |
| Applies to | pin prims (`pkg_lead`) of a component prototype |
| Requirement level | MUST (`pcba:pin:number`, `pcba:pin:solderable`); `crossSection`, `terminalType`, `designator` OPTIONAL |
| Tags | `pins`, `contacts`, `geometry`, `solder` |

## Summary

Every pin prim MUST carry `pcba:pin:number` — a stable id, **unique within the component** — and
`pcba:pin:solderable` (`bool`: does this contact form a solder joint?). `pcba:pin:crossSection`,
`pcba:pin:terminalType`, and `pcba:pin:designator` are OPTIONAL and validated when authored.
The board side never authors `pcba:pin:number`: a pad or barrel names a pin with
`pcba:board:componentPinNumber`.

This page follows PCBA to USD Input Contract **1.0.2**, section 10.

## Description

A pin is a contact **on a component** — a BGA ball, a gull-wing lead, an LGA land. Boards have
pads; a pin lands on a pad. Each pin is its own addressable `pkg_lead` prim in the shared
prototype, so its attributes are package data authored once:

- `pcba:pin:number` — the stable pin id (`"1"`, `"A1"`). It must identify exactly one pin,
  because a board site resolves its `pcba:board:componentPinNumber` against it
  ([BG.012](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)); two pins
  sharing a number leave a joint unresolvable. `pinCount` counts pin prims, so a duplicate does
  not surface there.
- `pcba:pin:solderable` — `true` means a joint forms here, so a `joint_roi` and solder-defect
  classes apply; `false` means it does not (a press-fit pin, a retention tab, a mechanical
  lead). Authored **per pin**, because one part's pins can differ; this — not `processClass` —
  is the authority on whether solder defects apply.
- `pcba:pin:crossSection` (OPTIONAL) — `circular rectangular other`; author when known and keep
  the full contour geometry for non-circular pins.
- `pcba:pin:terminalType` (OPTIONAL) — the terminal form, from a non-exhaustive vocabulary
  (`endTerminal gullwing jLead throughHolePin solderBall lLead cLead sideConcave cornerConcave
  flatInsulated qfn lcc lga solderColumn capae axial radial inline wire pressFit mixed
  otherThroughHole`). A form the source does not know is simply not authored. `pressFit` is a
  form; whether it takes solder is `solderable`, and the mount method stays `processClass`.
- `pcba:component:terminalTypes` (`token[]`, on the component) — MUST when a pin's
  `terminalType = mixed`: the actual forms the part combines, each a `terminalType` other than
  `mixed`.
- `pcba:pin:designator` (OPTIONAL) — the source netlist / CAD pin designator, preserved when
  `pcba:pin:number` is positional.

**Association is board-side.** The board prim (pad, barrel, paste) carries
`pcba:board:refdes` + `pcba:board:componentPinNumber`, not a bare `pcba:pin:number` — that would
read as though the board had pins. A bare board-side `pcba:pin:number` is read with a warning.

## Fields

| Attribute | On | Type | Req | Notes |
|-----------|----|------|-----|-------|
| `pcba:pin:number` | pin prim | `string` | MUST | Stable id, unique within the component; what `componentPinNumber` resolves against. |
| `pcba:pin:solderable` | pin prim | `bool` | MUST | Does this contact form a solder joint? Per pin. |
| `pcba:pin:crossSection` | pin prim | `token` | OPTIONAL | `circular rectangular other`; keep full contour geometry when non-circular. |
| `pcba:pin:terminalType` | pin prim | `token` | OPTIONAL | Terminal form from the (non-exhaustive) vocabulary above. |
| `pcba:component:terminalTypes` | component prim | `token[]` | MUST when a pin is `mixed` | The actual forms combined. |
| `pcba:pin:designator` | pin prim | `string` | OPTIONAL | Source pin designator when `number` is positional. |

## Why is it required?

- Solder-joint generation operates per contact; a non-unique pin number makes a board site
  ambiguous.
- `solderable` decides per pin whether solder-defect classes apply — a press-fit connector with
  one soldered ground pin is a real case a part-level switch gets wrong.
- Terminal form lets downstream pick applicable defect classes without inspecting geometry.

## Example

```usda
def Mesh "pin_1"
{
    token  pcba:mesh:role = "pkg_lead"
    token  pcba:mesh:matClass = "metal"
    string pcba:pin:number = "1"
    bool   pcba:pin:solderable = true
    token  pcba:pin:crossSection = "rectangular"     # optional
    token  pcba:pin:terminalType = "gullwing"        # optional
    string pcba:pin:designator = "41"                # optional: source designator
}
```

## How to comply

- Author `pcba:pin:number` (unique within the part) and `pcba:pin:solderable` on every pin prim
  of the prototype.
- Author `crossSection` / `terminalType` / `designator` where the source knows them; for
  `terminalType = mixed`, author `pcba:component:terminalTypes` on the component.
- Never author `pcba:pin:number` on a board prim; use `pcba:board:componentPinNumber`.

### What the checker proves

`PinGeometryChecker` fails a pin whose `pcba:pin:solderable` is absent (a `pcba:prov:solderable`
marker downgrades this to a declared gap) or is not a `bool`; fails an authored `crossSection`
or `terminalType` outside the vocabulary; fails a `mixed` pin whose component lacks a valid
`terminalTypes` list; warns on an authored-but-empty `designator`; and fails when two pins of one
component share a `pcba:pin:number`. Pins are discovered *by* `pcba:pin:number`, so a pin prim
lacking it is invisible to this rule rather than reported.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Pin Count (CG.005)](/capabilities/pcb_aoi/component_geometry/requirements/pin-count)
- [Hole Occupancy and Pin Association (BG.012)](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)
