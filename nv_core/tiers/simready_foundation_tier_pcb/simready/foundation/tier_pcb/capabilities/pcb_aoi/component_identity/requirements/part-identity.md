# Part Identity

| Code | CI.006 |
|------|------|
| Validator | `PartIdentityChecker` |
| Applies to | placed electrical component prim (discovered by `pcba:component:*`) |
| Requirement level | CONDITIONAL — author when known, never invent (N/A for `fiducial` / `mechanical`) |
| Tags | `parts` |

## Summary

Part identity is two independent groups: `pcba:component:mpn` + `pcba:component:manufacturer`
(the **manufacturer's** part identity) and `pcba:component:value` + `pcba:component:tolerance`
(the **electrical requirement** set by the designer). Both are CONDITIONAL: author them when
known and use null / empty — never an invented value — where not. `pcba:component:customerPartNumber`
(the board owner's internal part number) is also CONDITIONAL and often the only identity present
at design time.

This page follows PCBA to USD Input Contract **1.0.2**, section 8.

## Description

The two groups have different authors and different lifecycles, so they are authored and
validated separately:

- **`mpn` · `manufacturer`** — frequently **not fixed at design time**: many programs place an
  internal part number that maps to a bucket of approved equivalents, and operations picks the
  actual part later.
- **`value` · `tolerance`** — the electrical requirement (`10 ohm` / `±1%`), owned by the
  designer.
- **`customerPartNumber`** — the board owner's internal number. It carries real downstream
  meaning; author it when the source has it.

Together they distinguish parts that share a package but differ in identity — the basis for
wrong-part and wrong-value defect labelling — and set the expected top-marking for OCR. All are
Not Applicable for `fiducial` and `mechanical` placements.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:mpn` | `string` | CONDITIONAL | Manufacturer part number. Null / empty, never invented, when unknown. |
| `pcba:component:manufacturer` | `string` | CONDITIONAL | Component manufacturer. |
| `pcba:component:value` | `string` | CONDITIONAL | Electrical value (e.g. `10k`, `100nF`); empty for parts without one. |
| `pcba:component:tolerance` | `string` | CONDITIONAL | Tolerance (e.g. `±1%`). |
| `pcba:component:customerPartNumber` | `string` | CONDITIONAL | The board owner's internal part number. |

## Why is it required?

- Wrong-value and wrong-part defects are distinguishable only via this identity ground truth.
- Separating the manufacturer's identity from the electrical requirement matches how the data
  is actually owned and when it becomes known.

## Example

```usda
def Xform "U7" (
    instanceable = true
    prepend references = @./protos/QFN8.usda@</Proto>
)
{
    string pcba:component:refdes = "U7"
    string pcba:component:mpn = "STM32F407VGT6"
    string pcba:component:manufacturer = "ST"
    string pcba:component:value = "MCU"
    string pcba:component:tolerance = ""                      # declared, empty: not applicable
    string pcba:component:customerPartNumber = "032-26996-000"
}
```

## How to comply

- Author both groups on every electrical part from the BOM where known.
- Declare a field empty rather than inventing a value when it is inapplicable or not yet fixed.
- Author `customerPartNumber` whenever the source has it.

### What the checker proves

`PartIdentityChecker` requires `mpn`, `manufacturer`, `value`, and `tolerance` to be **declared**
on every electrical component (empty is accepted; a `pcba:prov:` marker downgrades an absent
field to a declared gap) and reports per group; it warns on a declared-but-empty
`customerPartNumber` and does not report its absence. Note the checker is stricter than the
contract's CONDITIONAL level here: an undeclared field fails, so declare unknown values as empty
strings.

## For More Information

- [PCB Component Identity](/capabilities/pcb_aoi/component_identity/capability-component_identity)
- [Component Manifest (CI.007)](/capabilities/pcb_aoi/component_identity/requirements/component-manifest)
