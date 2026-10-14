# Press-Fit State

| Code | CG.018 |
|------|------|
| Validator | _Not yet implemented_ |
| Applies to | components with `pcba:component:processClass = press_fit` and their pins |
| Requirement level | CONDITIONAL (applies when a part is press-fit) |
| Tags | `component`, `process-class`, `solder`, `conditional` |

## Summary

A `press_fit` part is a solderless through-hole part: its holes are plated, its barrels are
real and required, and the camera looks down them. Which of its contacts take solder — and
therefore which solder-defect classes apply — is determined **per pin** by `pcba:pin:solderable`,
not by the part-level process class.

This page follows PCBA to USD Input Contract **1.0.2**, sections 6, 10 and 12.

## Description

Press-fit is a third mount style alongside `SMT` and `through_hole`. This requirement adds no
attribute; it fixes the conditional behaviour around the existing ones:

- **Describe the hole.** A press-fit joint gets a `board_barrel` exactly like a soldered THT
  joint ([BG.003](/capabilities/pcb_aoi/board_geometry/requirements/hole-plating)), carrying the
  hole data and the `pcba:board:refdes` + `pcba:board:componentPinNumber` pair. Describing the
  hole and inspecting a solder joint are separate questions.
- **Decide solder per pin.** `processClass = press_fit` is a useful part-level hint, but
  `pcba:pin:solderable` is the authority: a press-fit connector with one soldered ground pin is
  a real case that a part-level switch gets wrong in both directions. Downstream suppresses
  solder-defect classes where `solderable = false` and applies them where `true`.
- **Lead form is separate.** `pcba:pin:terminalType = pressFit` describes the terminal form; it
  is neither the mount method nor the solderability.
- No paste is authored for press-fit contacts unless paste-in-hole applies
  ([BG.014](/capabilities/pcb_aoi/board_geometry/requirements/paste-in-hole)).

## Fields

| Attribute | On | Type | Req | Notes |
|-----------|----|------|-----|-------|
| `pcba:component:processClass = press_fit` | component | `token` | MUST for press-fit parts (CI.003) | Mount method; a hint, not the solder authority. |
| `pcba:pin:solderable` | each pin | `bool` | MUST (CG.007) | `false` on interference-fit pins; `true` on any pin that is soldered. |
| `board_barrel` at each joint | board | `Mesh` | MUST (BG.003) | Press-fit joints are described like any THT joint. |

## Why is it required?

- Injecting a solder defect on an unsoldered press-fit contact is physically meaningless and
  corrupts the ground truth; missing one on a soldered pin of a press-fit part loses a real
  defect class.
- The hole is still what the camera inspects, so barrels cannot be skipped for press-fit parts.

## Example

```usda
def Xform "X1" (
    instanceable = true
    prepend references = @./protos/PRESSFIT_HDR.usda@</Proto>
)
{
    string pcba:component:refdes = "X1"
    token  pcba:component:type = "connector"
    token  pcba:component:processClass = "press_fit"
}

# In the prototype:
def Mesh "pin_1"
{
    token pcba:mesh:role = "pkg_lead"
    string pcba:pin:number = "1"
    bool pcba:pin:solderable = false
    token pcba:pin:terminalType = "pressFit"
}
def Mesh "pin_G"
{
    token pcba:mesh:role = "pkg_lead"
    string pcba:pin:number = "G"
    bool pcba:pin:solderable = true
}
```

## How to comply

- Set `pcba:component:processClass = press_fit` on press-fit parts.
- Author `pcba:pin:solderable` per pin — `false` for interference-fit pins, `true` for any that
  are soldered.
- Author a `board_barrel` with the association pair at every press-fit joint.

No executable rule exists for this code; it is not part of the enforced feature set. The
underlying attributes are checked by CI.003, CG.007 and BG.003.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Pin Geometry (CG.007)](/capabilities/pcb_aoi/component_geometry/requirements/pin-geometry)
- [Process Class (CI.003)](/capabilities/pcb_aoi/component_identity/requirements/process-class)
