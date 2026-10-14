# Role/Material Consistency

| Code | UO.017 |
|------|------|
| Validator | `RoleMaterialConsistencyChecker` |
| Applies to | `every renderable Mesh with a determined-material role` |
| Requirement level | MUST |
| Tags | `organization` |

## Summary

Where a mesh's `pcba:mesh:role` determines its material class, the surface's material
MUST agree with that class. A copper-role surface bound to a solder-mask material (or
vice versa) is a defect: the role and the appearance disagree about what the surface
physically is.

## Description

Some roles fully determine the material of the surface they mark — an annular ring is
copper, a mask layer is mask, a paste deposit is solder. For those roles the derived
material class is fixed by the contract, and both the authored `pcba:mesh:matClass`
and the surface's material must agree with it. The checker infers a material
class from a direct binding target's name, with the coverage limits stated below.
It compares by **class/family**, not by concrete material name, so defect
material variants of the same class (e.g. a "BurntSolderPaste" variant of a solder
material) still match.

Derived classes by role:

| Role | Derived class |
|------|---------------|
| `board_copper`, `board_pad`, `board_barrel`, `board_testpoint`, `board_fiducial` | `copper` |
| `board_mask` | `mask` |
| `board_silk` | `silkscreen` |
| `board_paste` | `solder` |
| `board_substrate` | `other` |
| `pkg_lead` | `metal` |

Roles whose material is *not* determined are skipped, never failed:

- `pkg_body` / `pkg_lid` / `pkg_marking` — a body may be plastic, ceramic, or metal,
  so `matClass` is authored explicitly (CG.012) rather than derived.
- `board_misc` — a generic layer whose material is undetermined by definition.
- `board_hole` — a hole is an absence of material; the copper is the barrel.
- `fixture_*` — a carrier may be machined aluminium or a composite; `matClass` is
  authored explicitly.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:mesh:role` | `token` | MUST | The mesh role (UO.009); determines the class for the roles listed above. |
| `pcba:mesh:matClass` | `token` | MUST¹ | Per-surface material class (CG.012). ¹Required where the role does not determine it; where it does, it must agree. |

## Why is it required?

- A role/material disagreement means the asset is lying about what a surface is —
  either the role tag or the material is wrong, and downstream defect simulation
  keys off both.
- Checking by class rather than name keeps legitimate material variants (defect
  materials, vendor-specific shaders) from producing false positives.

## Example

```usda
def Mesh "pad_U7_1"
{
    token pcba:mesh:role = "board_pad"
    token pcba:mesh:matClass = "copper"   # agrees with the class board_pad derives
}
```

## How to comply

- For determined-material roles, ensure the surface's material class matches the
  table above (author `pcba:mesh:matClass` to match, and bind a material of that
  family).
- Do not tag a surface with a determined-material role as a workaround for a missing
  material — fix whichever of the two is wrong.

### What the checker proves

`RoleMaterialConsistencyChecker` compares the role's derived class with the material
names returned by a custom resolver for direct, all-purpose `material:binding`
relationships. The resolver follows ancestor bindings and `bindMaterialAs` strength;
prototype meshes are expanded into placed contexts. It also checks any authored
`pcba:mesh:matClass` against the derived class. Unknown material names and absent
bindings are skipped. CG.012 checks presence and vocabulary for roles that do not
derive their material class.

The custom resolver does not implement collection-based bindings or purpose-specific
bindings such as `material:binding:preview`. It is not equivalent to UsdShade's complete
binding resolution. Use the native USD material-binding API when inspecting those forms.

Two behaviours are pinned by tests: results are recomputed when an already validated stage is edited (the per-stage memo is invalidated by the stage's change notices), and a class mesh that wins deduplication is evaluated under the placed instances of the equivalent prototype content, not only in its library context.