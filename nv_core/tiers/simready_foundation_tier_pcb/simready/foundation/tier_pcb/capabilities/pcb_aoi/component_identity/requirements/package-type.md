# Package Type

| Code | CI.004 |
|------|------|
| Validator | `PackageTypeChecker` |
| Applies to | placed electrical component prim (discovered by `pcba:component:*`) |
| Requirement level | SHOULD (N/A for `fiducial` / `mechanical`) |
| Tags | `identity` |

## Summary

Every electrical component SHOULD carry `pcba:component:packageType` — a **string** naming the
package designation that identifies a specific physical body: a published standard (JEDEC,
JEITA, EIA, IEC — `QFN-48`, `0402`, `DIP-8`, `TO-99`) or, failing that, the manufacturer's
package designation. Not a lead-form or family word.

This page follows PCBA to USD Input Contract **1.0.2**, section 8.

## Description

The test for a good value: *could a reader obtain the physical dimensions from this string?*
`QFN-48`, `SOT-23-5`, and `0402` pass. Lead-form and family words — `LeadAxial`, `LeadRadial`,
`THConnector`, `ODD` — fail, because they describe a class of part and every dimension is still
unknown after reading them. Order of preference:

1. A **published standard** designation.
2. Failing that, the **manufacturer's** package designation — not portable across vendors, but
   it resolves to a real datasheet and a real body.
3. Failing both, **omit it** and record `pcba:prov:packageType = "not_yet_available"`.

It is a free string, not an enum, because the package space is open-ended. Lead form belongs in
`pcba:pin:terminalType`; mount method belongs in `pcba:component:processClass`. The field is
Not Applicable for `fiducial` and `mechanical` placements.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:packageType` | `string` | SHOULD | Standard (JEDEC / JEITA / EIA / IEC) or manufacturer package designation identifying a specific body. Never a family or lead-form word. |

## Why is it required?

- A body-identifying designation lets a consumer obtain real dimensions and group parts by
  physical package.
- A family word would validate clean while conveying no dimensions, which is worse than a
  declared gap.

## Example

```usda
def Xform "U7" (
    instanceable = true
    prepend references = @./protos/QFN8.usda@</Proto>
)
{
    string pcba:component:refdes = "U7"
    token  pcba:component:type = "ic"
    token  pcba:component:processClass = "SMT"
    string pcba:component:packageType = "QFN-8"
}
```

## How to comply

- Author `pcba:component:packageType` on every electrical part that has a standard or
  manufacturer designation.
- Where only a family or lead-form descriptor is available, omit the field and declare the gap
  with `pcba:prov:packageType`.

### What the checker proves

`PackageTypeChecker` warns when an electrical component has no `packageType` and fails when it
is declared but empty. It does not judge whether the string identifies a body rather than a
family, and it does not check fiducial or mechanical placements.

## For More Information

- [PCB Component Identity](/capabilities/pcb_aoi/component_identity/capability-component_identity)
- [Process Class (CI.003)](/capabilities/pcb_aoi/component_identity/requirements/process-class)
