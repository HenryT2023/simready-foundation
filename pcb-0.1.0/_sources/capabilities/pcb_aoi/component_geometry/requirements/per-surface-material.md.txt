# Per-Surface Material

| Code | CG.012 |
|------|------|
| Validator | `SurfaceMaterialChecker` |
| Applies to | every role-bearing `Mesh`; explicit authoring required on `pkg_*` and `fixture_*` |
| Requirement level | MUST on `pkg_*` / `fixture_*` meshes; derived from the role on `board_*` |
| Tags | `mesh`, `material`, `appearance` |

## Summary

`pcba:mesh:matClass` (`plastic metal ceramic solder mask copper silkscreen other`) names a
mesh's material class alongside its bound material. It MUST be authored explicitly on `pkg_*`
and `fixture_*` meshes, whose material is genuinely ambiguous. On `board_*` meshes it **derives
from the role** and need not be authored; any authored value must match the derivation.

This page follows PCBA to USD Input Contract **1.0.2**, section 9.

## Description

The pipeline needs the material class of each renderable surface without parsing shader
networks. For board geometry the role already determines it:

| Role | Derived `matClass` |
|------|--------------------|
| `board_substrate` | `other` |
| `board_copper` · `board_pad` · `board_barrel` · `board_fiducial` · `board_testpoint` | `copper` |
| `board_mask` | `mask` |
| `board_silk` | `silkscreen` |
| `board_paste` | `solder` |
| `pkg_lead` | `metal` (authored, and checked against this by UO.017) |
| `pkg_body` · `pkg_lid` · `pkg_marking` | none — ambiguous, MUST be authored |
| `fixture_carrier` | none — MUST be authored |
| `board_misc` · `board_hole` | none — no class derived or required |

`pkg_lead` is `metal`, not `solder`: `matClass` describes the lead's own material as delivered,
and a solder finish is a plating on top of it — an as-delivered component carries no solder.
Where an exporter cannot substantiate a value (a fixture from a STEP file with no material
data), omit it and declare the gap with `pcba:prov:matClass` rather than authoring a rendering
default as though it were data. Role and bound material must agree by class
([UO.017](/capabilities/pcb_aoi/usd_organization/requirements/role-material)).

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:mesh:matClass` | `token` | MUST on `pkg_*` and `fixture_*`; derived on `board_*` | `plastic metal ceramic solder mask copper silkscreen other`. An authored value on a board mesh must match the derivation. |

## Why is it required?

- A body may be plastic or ceramic and a carrier aluminium or composite; nothing but the
  exporter can say which.
- Deriving the class for board roles removes redundant authoring while keeping the class
  available to every consumer.

## Example

```usda
def Mesh "Body"
{
    token pcba:mesh:role = "pkg_body"
    token pcba:mesh:matClass = "plastic"
}
def Mesh "pin_1"
{
    token pcba:mesh:role = "pkg_lead"
    token pcba:mesh:matClass = "metal"
}

def Mesh "TopCopper"
{
    token pcba:mesh:role = "board_copper"      # matClass derives to copper; authoring it is optional
}
```

## How to comply

- Author `pcba:mesh:matClass` on every `pkg_*` and `fixture_*` mesh from the vocabulary.
- Omit it on `board_*` meshes, or author the derived value.
- Declare an unknown class with `pcba:prov:matClass`; never invent one.

### What the checker proves

`SurfaceMaterialChecker` fails a `pkg_*` or `fixture_*` mesh with no `matClass` (a
`pcba:prov:matClass` marker downgrades this to a declared gap), and fails any authored value that
is empty or outside the vocabulary, on any role. It does not verify that an authored board-mesh
value matches the role derivation; agreement with the bound material is UO.017.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Nominal Appearance (CG.011)](/capabilities/pcb_aoi/component_geometry/requirements/nominal-appearance)
- [Role/Material Consistency (UO.017)](/capabilities/pcb_aoi/usd_organization/requirements/role-material)
