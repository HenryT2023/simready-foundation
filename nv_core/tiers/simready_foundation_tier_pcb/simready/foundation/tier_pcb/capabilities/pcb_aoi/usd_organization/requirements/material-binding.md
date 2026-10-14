# Material Binding

| Code | UO.011 |
|------|------|
| Validator | `MaterialBindingChecker` |
| Applies to | renderable meshes; checked on component (`pkg_*`) meshes |
| Requirement level | SHOULD (advisory check) |
| Tags | `organization` |

## Summary

Renderable meshes SHOULD carry a bound material so the board renders with its nominal
appearance. Board copper and mask geometry with production-accurate materials is required by
[BG.002](/capabilities/pcb_aoi/board_geometry/requirements/copper-mask-geometry); the bound
material's class must agree with the mesh role
([UO.017](/capabilities/pcb_aoi/usd_organization/requirements/role-material)).

This page follows PCBA to USD Input Contract **1.0.2**, sections 3, 5 and 9.

## Description

The desirable layout carries a `Looks/` scope with one material per role class (copper, mask,
paste, substrate, body, lead, …), bound through the standard `material:binding` relationship.
Materials are approximate at input time — the pipeline randomizes appearance downstream — so
the contract does not make the binding itself a hard requirement on every mesh; it requires
that where a material *is* bound it agrees with the role by class (UO.017), and that copper and
mask geometry exist with materials that give production-accurate board colour (BG.002).

The semantic material class is a separate attribute, `pcba:mesh:matClass`
([CG.012](/capabilities/pcb_aoi/component_geometry/requirements/per-surface-material)): required
explicitly on `pkg_*` and `fixture_*` meshes, whose material is genuinely ambiguous, and derived
from the role on `board_*` meshes. Where an exporter cannot substantiate a class, it declares
the gap with `pcba:prov:matClass` rather than authoring a rendering default as data.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `material:binding` | `rel` | SHOULD | Standard USD binding to a `UsdShade.Material` of the role's class. |
| `pcba:mesh:matClass` | `token` | MUST on `pkg_*` / `fixture_*`; derived on `board_*` | `plastic metal ceramic solder mask copper silkscreen other` (CG.012). |

## Why is it required?

- A bound material is what makes the mesh render; component bodies and leads without one
  render with a fallback that misrepresents the part.
- Pairing the binding with a semantic `matClass` lets the pipeline reason about surfaces
  without parsing shader networks.

## Example

```usda
def Mesh "Body" (
    prepend apiSchemas = ["MaterialBindingAPI"]
)
{
    token pcba:mesh:role = "pkg_body"
    token pcba:mesh:matClass = "plastic"
    rel material:binding = </Board/Looks/EpoxyBlack>
}
```

## How to comply

- Bind a `UsdShade.Material` of the matching class to component and board meshes.
- Author `pcba:mesh:matClass` on `pkg_*` and `fixture_*` meshes; let it derive for board roles.
- Keep binding and class consistent so UO.017 passes.

### What the checker proves

`MaterialBindingChecker` is advisory: it warns for each `pkg_*` mesh with no direct
`material:binding` target. It does not check board meshes, the material's contents, or
`matClass` (CG.012 and UO.017 do).

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Per-Surface Material (CG.012)](/capabilities/pcb_aoi/component_geometry/requirements/per-surface-material)
- [Role/Material Consistency (UO.017)](/capabilities/pcb_aoi/usd_organization/requirements/role-material)
