# Markings

| Code | CG.010 |
|------|------|
| Validator | `MarkingsChecker` |
| Applies to | `placed component prim` and its `pkg_marking` meshes |
| Requirement level | CONDITIONAL — when markings are present (N/A for `fiducial` / `mechanical`) |
| Tags | `component`, `markings`, `ocr`, `ground-truth` |

## Summary

`pcba:component:markings` (a string) records the visible marking text on the
component. It is required when markings are present and is the ground truth for
OCR and wrong-part inspection.

## Description

Many components carry visible text — a top-code, part marking, date code, or
value print. The AOI pipeline reads these markings to verify the correct part is
placed (wrong-part detection) and to train OCR / text-grounding tasks.
`pcba:component:markings` records the expected marking string, giving the OCR
ground truth for the sample.

The attribute is conditional: it MUST be authored when the part carries a visible
marking and MAY be omitted for an unmarked part. As with polarity
([CG.009](/capabilities/pcb_aoi/component_geometry/requirements/polarity)), the
marking is authored as **standalone `pkg_marking` geometry**, not baked into the
body texture, so it can be manipulated and referenced as a discrete feature.
Per-instance markings (serials, date codes, part-specific top-codes) are authored
per instance rather than shared on the prototype.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:markings` | `string` | MUST when markings present | Visible marking text; OCR / wrong-part ground truth |

## Why is it required?

- Marking text is the ground truth for OCR training and wrong-part detection;
  without it those samples cannot be scored.
- Recording the expected string on the prim removes any need to re-read the
  rendered image to recover the label.

## Example

```usda
def Xform "U7"
{
    string pcba:component:markings = "STM32F407"

    def Mesh "TopCode"
    {
        token pcba:mesh:role = "pkg_marking"
    }
}
```

## How to comply

- Author `pcba:component:markings` with the true visible marking text whenever the
  part is marked.
- Author the marking as standalone `pkg_marking` geometry, not a baked texture.
- Author per-instance markings (serial, date code) on the instance, not the
  shared prototype.

### What the checker proves

`MarkingsChecker` is advisory: it warns only when `pcba:component:markings` is declared but empty.
Whether a part has visible markings is not detectable from the asset, so absence is never
reported, and the standalone-geometry rule for `pkg_marking` meshes is not machine-checked.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Polarity (CG.009)](/capabilities/pcb_aoi/component_geometry/requirements/polarity)
