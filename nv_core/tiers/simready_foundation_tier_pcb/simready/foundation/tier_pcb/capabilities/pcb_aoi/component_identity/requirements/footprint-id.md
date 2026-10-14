# Footprint Id

| Code | CI.005 |
|------|------|
| Validator | `FootprintIdChecker` |
| Applies to | placed electrical component prim (discovered by `pcba:component:*`) |
| Requirement level | MUST (N/A for `fiducial` / `mechanical`); `sourceOrigin` MUST when the id is source-specific |
| Tags | `identity` |

## Summary

Every electrical component MUST carry `pcba:component:footprintId`, identifying the
**footprint** — the set of pads (and holes, for THT) the part lands on — in the source CAD
library. When that id is source-specific, the prim MUST also carry
`pcba:component:sourceOrigin`, which says where the footprint came from and therefore how far
to trust it.

This page follows PCBA to USD Input Contract **1.0.2**, sections 1.1 and 8.

## Description

A footprint is **not a prim** in the delivered USD — there is no footprint container. Pads are
grouped bottom-up by association: "the pads of `U7`" is every `board_pad` whose
`pcba:board:refdes` is `"U7"`. `footprintId` is the pointer back into the library that defined
that layout.

`sourceOrigin` is a free string on the **trust axis**, with a non-exhaustive starting
vocabulary: `cad_authored` (the designer's own land pattern) · `cad_derived` (reconstructed by
the extractor — inferred, not stated) · `library_vendor` · `library_site` · `library_shape` (a
land pattern, not a full part) · `manually_authored` · `placeholder_named` (a footprint named
on a component list but never resolved — the outline is a default) · `placeholder_generated`
(neither name nor source — fully fabricated). Dimensions from either `placeholder_*` token are
fabricated; do not measure against them. Keep values stable once shipped.

Both fields are Not Applicable for `fiducial` and `mechanical` placements.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:footprintId` | `string` | MUST (electrical) | Identifies the footprint in the source CAD library. |
| `pcba:component:sourceOrigin` | `string` | MUST when `footprintId` is source-specific | Where the footprint came from; starting vocabulary above, extendable. |

## Why is it required?

- The pipeline needs a stable pointer from a component to the land pattern its pads realize.
- `sourceOrigin` tells a consumer how much to trust the footprint's dimensions — a placeholder
  outline must not be measured against.

## Example

```usda
def Xform "U7" (
    instanceable = true
    prepend references = @./protos/QFN8.usda@</Proto>
)
{
    string pcba:component:refdes = "U7"
    string pcba:component:footprintId = "QFN8_3x3"
    string pcba:component:sourceOrigin = "library_vendor"
}
```

## How to comply

- Author `pcba:component:footprintId` on every electrical part from the source library name.
- When the id is only meaningful within its source, also author `sourceOrigin`; use a
  `placeholder_*` token honestly when the outline is a default.

### What the checker proves

`FootprintIdChecker` fails an electrical component whose `footprintId` is absent (a
`pcba:prov:footprintId` marker downgrades this to a declared gap) or empty. It does not check
`sourceOrigin` at all — presence, vocabulary, or whether the id is source-specific.

## For More Information

- [PCB Component Identity](/capabilities/pcb_aoi/component_identity/capability-component_identity)
- [Pad Number (BG.005)](/capabilities/pcb_aoi/board_geometry/requirements/pad-number)
