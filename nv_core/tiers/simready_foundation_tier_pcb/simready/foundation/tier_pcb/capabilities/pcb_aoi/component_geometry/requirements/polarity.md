# Polarity

| Code | CG.009 |
|------|------|
| Validator | `PolarityChecker` |
| Applies to | `placed component prim` and its `pkg_marking` meshes |
| Requirement level | CONDITIONAL — when the part is polarized / carries a marker (N/A for `fiducial` / `mechanical`) |
| Tags | `component`, `polarity`, `markings`, `orientation`, `ground-truth` |

## Summary

`pcba:component:polarityType` (a token) names how a polarized part indicates its
polarity. It is required for polarized parts and is the ground truth for
reverse-polarity defects. Pin-1 / polarity / marking features MUST be authored as
**standalone geometry** (`pkg_marking`), never baked into a texture.

## Description

Reverse-polarity is a distinct AOI defect class: a diode, electrolytic
capacitor, or keyed part installed backwards. To generate and score it, the
pipeline needs to know **how** the part signals its polarity.
`pcba:component:polarityType` names the indicator:

- `dot` — a printed pin-1 / polarity dot.
- `notch` — a package notch or keyway.
- `bevel` — a bevelled edge / chamfer.
- `band` — a cathode / polarity band.
- `plus` — a printed `+` marking.
- `text` — a polarity indicated by text.
- `asymmetric` — an asymmetric body shape that reads as polarity.

**When a part carries a pin-1 or polarity marker**, that marker — like any label — MUST be
**standalone geometry** carrying `pcba:mesh:role = pkg_marking`. Not every part has one: plenty
of genuinely interchangeable parts are unmarked, so this is conditional on the marker existing,
not a demand that one be invented. It MUST NOT be
baked into the body texture. Standalone marking geometry lets the pipeline move,
hide, or re-orient the indicator to synthesize reverse-polarity and
wrong-orientation samples, and lets grounding annotations reference it as a
discrete feature.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:polarityType` | `token` | MUST when polarized | `dot`, `notch`, `bevel`, `band`, `plus`, `text`, `asymmetric` |
| `pcba:mesh:role = pkg_marking` | `token` (on marking mesh) | MUST when a marker exists | Polarity / pin-1 / marking features are standalone geometry, not baked into texture |

## Why is it required?

- Reverse-polarity is a distinct defect class; the pipeline cannot synthesize or
  score it without knowing the polarity indicator.
- Standalone `pkg_marking` geometry (rather than a baked texture) lets the
  pipeline manipulate the indicator to generate orientation / polarity samples
  and lets annotations reference it directly.

## Example

```usda
def Xform "D4"
{
    token pcba:component:polarityType = "band"

    def Mesh "CathodeBand"
    {
        token pcba:mesh:role = "pkg_marking"
    }
}
```

## How to comply

- Author `pcba:component:polarityType` on every polarized part.
- Author the polarity / pin-1 / marking indicators as standalone meshes with
  `pcba:mesh:role = pkg_marking`; never bake them into the body texture.

### What the checker proves

`PolarityChecker` fails an authored `polarityType` outside the vocabulary. Whether a part is
polarized is not detectable from geometry, so absence is never reported, and the
standalone-`pkg_marking` rule is not machine-checked.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Pin-1 Position (CG.008)](/capabilities/pcb_aoi/component_geometry/requirements/pin1-position)
- [Markings (CG.010)](/capabilities/pcb_aoi/component_geometry/requirements/markings)
