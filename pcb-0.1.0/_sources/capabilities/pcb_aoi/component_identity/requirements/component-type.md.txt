# Component Type

| Code | CI.002 |
|------|------|
| Validator | `ComponentTypeChecker` |
| Applies to | placed electrical component prim (discovered by `pcba:component:*`) |
| Requirement level | MUST (N/A for `fiducial` / `mechanical`) |
| Tags | `identity` |

## Summary

Every electrical component prim MUST carry `pcba:component:type`, a token from
`resistor capacitor inductor led diode transistor connector crystal switch ic other`. It is
authored / classified — **not inferred from the refdes prefix**.

This page follows PCBA to USD Input Contract **1.0.2**, sections 8 and 8.1.

## Description

`pcba:component:type` classifies what kind of part this is and builds the type → instances map
that defect targeting keys off (e.g. applying a defect class only to `capacitor` instances).
Refdes conventions vary between sources and are not authoritative, so the value is drawn from
the BOM / component library or an explicit classification step. It is Not Applicable for
`fiducial` and `mechanical` placements, which have no electrical identity. Where the class
genuinely cannot be resolved, defer with `pcba:prov:type = "not_yet_available"` rather than
guessing.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:type` | `token` | MUST (electrical) | `resistor capacitor inductor led diode transistor connector crystal switch ic other`. Not derived from `refdes`. |

## Why is it required?

- Defect targeting needs a type → instances map so a defect class reaches the right parts.
- Refdes prefixes are non-authoritative, so type must be authored to be trustworthy.

## Example

```usda
def Xform "U7" (
    instanceable = true
    prepend references = @./protos/QFN8.usda@</Proto>
)
{
    string pcba:component:refdes = "U7"
    token  pcba:component:type = "ic"
}
```

## How to comply

- Author `pcba:component:type` on every electrical component from the vocabulary.
- Source it from the BOM / library or an explicit classification — not from the refdes.

### What the checker proves

`ComponentTypeChecker` fails an electrical component whose `type` is absent (a `pcba:prov:type`
marker downgrades this to a declared gap), empty, or outside the vocabulary. It skips fiducial
and mechanical placements and does not judge whether the chosen type is correct.

## For More Information

- [PCB Component Identity](/capabilities/pcb_aoi/component_identity/capability-component_identity)
