# Nominal Appearance

| Code | CG.011 |
|------|------|
| Validator | `AppearanceChecker` |
| Applies to | `placed component prim` |
| Requirement level | MUST for electrical parts; SHOULD for `fiducial` / `mechanical` |
| Tags | `component`, `appearance`, `material` |

## Summary

Every component MUST carry a representative nominal appearance:
`pcba:component:bodyColorNominal` (a `color3f`), `pcba:component:finishNominal` (a
token: `matte`, `gloss`, `metallic`, `other`), and
`pcba:component:materialClassNominal` (a token: `plastic`, `metal`, `ceramic`,
`solder`, `other`).

## Description

The pipeline needs a **representative** appearance for each component so it can
render a plausible known-good sample and randomize appearance for augmentation.
These are nominal values — a reasonable, library-level description of the part's
look — **not a photoreal specification**; the augmentation stage handles
photorealism.

- `pcba:component:bodyColorNominal` — the nominal body colour as a linear
  `color3f`.
- `pcba:component:finishNominal` — the surface finish: `matte`, `gloss`,
  `metallic`, or `other`.
- `pcba:component:materialClassNominal` — the dominant material class of the body:
  `plastic`, `metal`, `ceramic`, `solder`, or `other`.

All three are MUST fields on electrical parts and SHOULD on fiducial / mechanical placements
(author them when meaningful; they are not gated). They describe the component as a whole; per-surface
material is captured separately by
[CG.012](/capabilities/pcb_aoi/component_geometry/requirements/per-surface-material).

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:bodyColorNominal` | `color3f` | MUST | Representative body colour (linear); not photoreal |
| `pcba:component:finishNominal` | `token` | MUST | `matte`, `gloss`, `metallic`, `other` |
| `pcba:component:materialClassNominal` | `token` | MUST | `plastic`, `metal`, `ceramic`, `solder`, `other` |

## Why is it required?

- A representative appearance lets the pipeline render a plausible known-good
  sample without a full material library per part.
- Nominal colour / finish / material give the augmentation stage a base to
  randomize from, keeping generated appearance in a realistic range.

## Example

```usda
def Xform "U7"
{
    color3f pcba:component:bodyColorNominal = (0.05, 0.05, 0.05)
    token pcba:component:finishNominal = "matte"
    token pcba:component:materialClassNominal = "plastic"
}
```

## How to comply

- Author all three nominal appearance attributes on every component.
- Use library-level representative values; do not attempt a photoreal
  specification here.
- Draw `finishNominal` and `materialClassNominal` from the allowed token sets.

### What the checker proves

`AppearanceChecker` runs on electrical components only. It fails an absent `bodyColorNominal`,
and an absent, empty, or out-of-vocabulary `finishNominal` or `materialClassNominal`; a matching
`pcba:prov:` marker downgrades an absent field to a declared gap. It does not judge whether the
values are representative.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Per-Surface Material (CG.012)](/capabilities/pcb_aoi/component_geometry/requirements/per-surface-material)
