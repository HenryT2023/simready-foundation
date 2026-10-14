# Component Manifest

| Code | CI.007 |
|------|------|
| Validator | _Not yet implemented_ |
| Applies to | placed component prim (discovered by `pcba:component:*`) |
| Requirement level | MUST |
| Tags | `identity` |

## Summary

The board MUST provide a component manifest: one record per placed component linking its BOM
identity, its footprint, and its component asset. This is realized **without a separate sidecar**
— the per-instance `pcba:component:*` attributes plus the prim's prototype `reference` are that
record, distributed across the stage, and the `pcba:board:members` registry indexes it.

This page follows PCBA to USD Input Contract **1.0.2**, sections 3, 4 and 8.

## Description

The source requirement calls for one record per reference designator and does not prescribe a
storage format, so the contract satisfies it from what is already authored on each placed
component prim:

- **Identity** — `pcba:component:refdes` (or `instanceId`), `type`, `processClass`
  (CI.001–CI.003).
- **BOM identity** — `mpn` / `manufacturer`, `value` / `tolerance`, `customerPartNumber`
  (CI.006).
- **Footprint** — `footprintId` with `sourceOrigin` (CI.005); `packageType` (CI.004).
- **Component asset** — the prim's prototype `reference` (the shared prototype, authored once
  and instanced per placement).

Because every placed component carries these attributes and references a prototype, the
manifest exists as per-prim state that cannot drift from the stage. The optional
`Registries` scope ([UO.008](/capabilities/pcb_aoi/usd_organization/requirements/registries))
enumerates the records; it is an index, not their authority. This record is distinct from the
UO.013 `pcba:board:packageManifest`, which inventories packaged *files*.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| _(no single attribute)_ | — | MUST | One record per placed component, assembled from the CI.001–CI.006 attributes plus the prototype `reference`. No sidecar file. |

## Why is it required?

- Consumers need one per-part record tying identity, footprint, and the asset that places
  it.
- Distributed per-prim attributes stay in sync with the stage automatically.

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
    string pcba:component:footprintId = "QFN8_3x3"
    string pcba:component:mpn = "STM32F407VGT6"
    string pcba:component:manufacturer = "ST"
    string pcba:component:value = "MCU"
    string pcba:component:tolerance = ""
}
```

## How to comply

- Author the identity attributes (CI.001–CI.006) on every placed component prim and reference
  the shared prototype that provides its geometry.
- Do not emit a separate manifest sidecar.
- Keep this record distinct from `pcba:board:packageManifest` (UO.013).

No executable rule exists for this code; it is not part of the enforced feature set. Its
constituent attributes are checked by CI.001–CI.006.

## For More Information

- [PCB Component Identity](/capabilities/pcb_aoi/component_identity/capability-component_identity)
- [Package Manifest (UO.013)](/capabilities/pcb_aoi/usd_organization/requirements/package-manifest)
