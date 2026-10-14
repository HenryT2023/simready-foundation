# Mesh Role

| Code | UO.009 |
|------|------|
| Validator | `MeshRoleChecker` |
| Applies to | every `Mesh` |
| Requirement level | MUST |
| Tags | `organization` |

## Summary

Every `Mesh` on the board MUST carry `pcba:mesh:role`, a token from the contract vocabulary that
names what the geometry *is*. The role is **authoritative** — a prim name may supplement it but
must never replace it.

This page follows PCBA to USD Input Contract **1.0.2**, section 9.

## Description

`pcba:mesh:role` is the primary discovery key for geometry: every downstream operation finds
bodies, leads, pads, barrels, copper, and substrate by role. Prim names are non-normative.

### Vocabulary

- **Component:** `pkg_body` · `pkg_lead` · `pkg_lid` · `pkg_marking`
- **Board:** `board_substrate` · `board_copper` · `board_mask` · `board_pad` · `board_paste` ·
  `board_hole` · `board_barrel` · `board_fiducial` · `board_silk` · `board_testpoint` ·
  `board_misc`
- **Fixture:** `fixture_carrier` — tooling the board or panel is mounted into, not part of the
  fabricated board; SHOULD state its step in `pcba:fixture:process`.

Notes on the tokens:

- `board_fiducial` and `board_silk` are their own roles — do not fold them into `board_copper`.
- `board_testpoint` is exposed copper placed for electrical test: not a `board_pad` (no
  terminal lands on it) and not lost into `board_copper`.
- `board_misc` is the escape hatch for board geometry with no other token (a dielectric layer,
  say). It is exempt from the role/material rule. It is not a dumping ground.
- `board_barrel` is the plating through a hole and carries the hole data; `board_hole` is
  optional bookkeeping ([BG.003](/capabilities/pcb_aoi/board_geometry/requirements/hole-plating)).
- **No solder roles.** There is no `board_solder` and no `pkg_solder`: solder joints are
  generated downstream. Strip pre-attached solder from library parts before export.

Role and bound material must agree by class
([UO.017](/capabilities/pcb_aoi/usd_organization/requirements/role-material)); `matClass` is
authored explicitly on `pkg_*` and `fixture_*` meshes and derives from the role for `board_*`
([CG.012](/capabilities/pcb_aoi/component_geometry/requirements/per-surface-material)).

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:mesh:role` | `token` | MUST | Authoritative geometry role from the vocabulary above. No `board_solder` / `pkg_solder`. |

## Why is it required?

- Every defect operation discovers geometry by role; an untagged mesh cannot be classified.
- Prim names vary by exporter and are non-authoritative, so the token is the only portable
  identifier.

## Example

```usda
def Mesh "Substrate"
{
    token pcba:mesh:role = "board_substrate"
}
def Mesh "TopSilk"
{
    token pcba:mesh:role = "board_silk"
}

def Xform "Proto"
{
    def Mesh "Body"
    {
        token pcba:mesh:role = "pkg_body"
        token pcba:mesh:matClass = "plastic"
    }
    def Mesh "Pin1Dot"
    {
        token pcba:mesh:role = "pkg_marking"
        token pcba:mesh:matClass = "plastic"
    }
    def Scope "Pins"
    {
        def Mesh "pin_1"
        {
            token pcba:mesh:role = "pkg_lead"
            token pcba:mesh:matClass = "metal"
        }
    }
}
```

## How to comply

- Author `pcba:mesh:role` on **every** `Mesh` from the vocabulary; never rely on prim names.
- Use the specific role where one exists (`board_silk`, `board_fiducial`, `board_testpoint`)
  before reaching for `board_copper` or `board_misc`.
- Author no solder geometry on the board or on components.

### What the checker proves

`MeshRoleChecker` fails any `Mesh` without `pcba:mesh:role` and any role outside the vocabulary;
the deprecated `pkg_solder` produces a warning naming the reason. It does not judge whether the
chosen role is the *right* one for the geometry (a mask layer tagged `board_misc` passes).

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Role/Material Consistency (UO.017)](/capabilities/pcb_aoi/usd_organization/requirements/role-material)
