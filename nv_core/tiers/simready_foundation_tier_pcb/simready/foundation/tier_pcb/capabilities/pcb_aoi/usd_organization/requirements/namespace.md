# Namespace

| Code | UO.010 |
|------|------|
| Validator | `NamespaceChecker` |
| Compatibility | {compatibility}`open-usd` |
| Applies to | custom PCB contract attributes |
| Requirement level | MUST for PCB contract attributes; the `pcb:` spelling and typo checks are advisory |
| Tags | `organization` |

## Summary

Author PCB contract metadata under **`pcba:`**, with colon-delimited scopes and
lower-camelCase leaf names. Use ordinary custom USD attributes: no custom schema,
schema fallback, or plugin is required. Other domains' properties retain their
own namespaces.

This page follows PCBA to USD Input Contract **1.0.2**, sections 1, 11 and 14.

## Description

The contract recognizes nine scopes:

| Scope | Purpose |
|-------|---------|
| `pcba:component:` | component identity, placement, and package data |
| `pcba:mesh:` | geometry role and material class |
| `pcba:pin:` | component terminal identity and properties |
| `pcba:board:` | board-root metadata and board sites, pads, barrels, and registries |
| `pcba:prov:` | deferral markers; the leaf is the missing field's bare leaf name |
| `pcba:layer:` | optional descriptive layer metadata |
| `pcba:panel:` | panel-to-board relationships |
| `pcba:fixture:` | tooling dimensions and assembly process |
| `pcba:variance:` | optional manufacturer-supplied package tolerances |

The shorter `pcb:` spelling is also read, with an advisory warning; author
`pcba:`. Unknown PCB scopes are likely typos
and produce warnings rather than hard failures. This does not prohibit standard
USD properties or custom metadata belonging to other domains.

### Manufacturing variance carrier

Author `pcba:variance:*` on the **component (package prototype) prim**, alongside
its package data, once for all placed instances. These fields describe all
through-hole pins of that package type; they are not per-placement measurements
and do not belong on the board root. In a mixed-terminal package they do not
cover its SMT pins.

| Attribute | Type | Meaning |
|-----------|------|---------|
| `pcba:variance:thtPinTiltToleranceDeg` | `float` | maximum tilt from the hole axis |
| `pcba:variance:thtPinOffsetToleranceMm` | `float` | maximum lateral offset in the bore |
| `pcba:variance:thtPinExtrusionToleranceMm` | `float2` | absolute minimum and maximum protrusion past the solder-side face |
| `pcba:variance:thtPinCutEndProfileList` | `token[]` | permitted pin-end forms, such as `straightCut` and `roundedEdge` |

All are optional. Author them only from measured process-preparation or BOM data;
omit unavailable values without a provenance marker. Geometry always represents
the nominal: a consumer can ignore variance and still render the nominal board.

## Why is it required?

Consistent scopes let consumers discover domain metadata without depending on
prim names, while keeping component, board, fixture, and package facts distinct.

## Examples

```usda
def Xform "R12"
{
    custom string pcba:component:refdes = "R12"
    custom token pcba:component:type = "resistor"
    custom float pcba:component:nominalRotationDeg = 90.0
    custom string pcba:prov:markings = "not_yet_available"
}
```

## How to comply

Use the scope for the concept being authored and lower-camelCase leaf names.
Keep deferral markers on the prim that would carry the real field. Put package
variance on the component prototype and board provenance on the board root.

`NamespaceChecker` checks recognized prefixes on discovered components and
role-bearing meshes. It does not validate all property types, leaf names,
variance values, or the variance carrier. Those obligations need separate
inspection. For advisory-report visibility, see the
[PCB-Assembly guide](/profiles/pcb_assembly).
