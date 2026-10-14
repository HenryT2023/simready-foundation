# Pin Pitch

| Code | CG.006 |
|------|------|
| Validator | `PinPitchChecker` |
| Applies to | `placed component prim` |
| Requirement level | CONDITIONAL — when meaningful; omit for 2-terminal passives (N/A for `fiducial` / `mechanical`) |
| Tags | `component`, `pins`, `geometry` |

## Summary

`pcba:component:pinPitchMm` (a float, in millimetres) gives the centre-to-centre
spacing between adjacent contacts. It is required when meaningful and is omitted
for 2-terminal passives.

## Description

`pcba:component:pinPitchMm` is the nominal contact pitch — the distance between
the centres of adjacent pins — in millimetres. For a regular multi-pin package
(QFN, QFP, SOIC, connector), pitch is a well-defined single value that the
pipeline uses to reason about contact spacing, bridging likelihood, and
fine-pitch defect classes.

Pitch is a **conditional** field: for a 2-terminal passive (a chip resistor or
capacitor) there is no meaningful pitch, and the attribute MUST be omitted rather
than filled with a placeholder. If the package has an irregular or multi-pitch
arrangement where a single value is not representative, omit it and rely on the
per-pin geometry ([CG.007](/capabilities/pcb_aoi/component_geometry/requirements/pin-geometry))
and pin-1 position ([CG.008](/capabilities/pcb_aoi/component_geometry/requirements/pin1-position))
instead.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:pinPitchMm` | `float` | MUST when meaningful | Centre-to-centre contact spacing in mm; omit for 2-terminal passives |

## Why is it required?

- Contact pitch drives fine-pitch defect classes (bridging, insufficient
  clearance) and lets the pipeline reason about spacing without measuring
  geometry.
- Making it conditional avoids inventing a meaningless value for 2-terminal
  passives, which would pollute the ground truth.

## Example

```usda
def Xform "U7"
{
    float pcba:component:pinPitchMm = 0.5
}
```

## How to comply

- Author `pcba:component:pinPitchMm` for regular multi-pin packages.
- Omit it entirely for 2-terminal passives or where a single pitch is not
  representative — do not use a placeholder such as `0`.

### What the checker proves

`PinPitchChecker` requires `pinPitchMm` to be declared whenever `pcba:component:pinCount` is
greater than 2 (a `pcba:prov:pinPitchMm` marker downgrades absence to a declared gap); parts with
two or fewer pins, or no declared `pinCount`, are skipped. It does not check the value against
the pin geometry, and it cannot recognise an irregular multi-pitch part for which omission is
the right answer — declare the gap there.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Pin Geometry (CG.007)](/capabilities/pcb_aoi/component_geometry/requirements/pin-geometry)
