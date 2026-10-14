# Registries

| Code | UO.008 |
|------|------|
| Validator | `RegistriesChecker` |
| Applies to | a `Registries` scope carrying `rel pcba:board:members` |
| Requirement level | SHOULD |
| Tags | `organization` |

## Summary

The board SHOULD expose a component registry: a `Registries` scope carrying
`rel pcba:board:members` that targets **every placed component on the board, all mount
classes**, so a consumer can enumerate parts without a full stage traversal. The registry is
an **index, not a source of truth**.

This page follows PCBA to USD Input Contract **1.0.2**, section 3.

## Description

A consumer that wants the parts list resolves the registry, reads `pcba:board:members`, and
follows the targets to the component prims. Two points from the contract:

- **It covers all mount classes**, not just through-hole. A subset — the THT parts, say — is a
  selection by `pcba:component:processClass`; that is what the attribute is for. Do **not**
  author parallel per-class registries.
- **It is an index.** `processClass` and the component prims are authoritative; a registry
  that disagrees with them is wrong, not a second opinion. It is SHOULD rather than MUST for
  exactly that reason: a stale or over-inclusive registry is worse than none, because a
  consumer trusting it gets a confidently wrong answer.

Within a panel the registry lives on the board master and resolves per position.

## Fields

| Attribute | On | Type | Req | Notes |
|-----------|----|------|-----|-------|
| `pcba:board:members` | a `Registries` scope | `rel` | SHOULD | Targets every placed component prim (SMT, through-hole, press-fit, fiducial, mechanical). |

## Why is it required?

- Enumerating by registry avoids an O(stage) traversal and keeps discovery independent of prim
  naming.
- Keeping one registry for all classes matches the contract's one-model design; a subset is a
  filter, not a separate list.

## Example

```usda
def Scope "Registries"
{
    def Scope "Components"
    {
        rel pcba:board:members = [
            </Board/Layers/Top/Components/U7>,       # SMT
            </Board/THT/J1>,                         # through_hole
            </Board/Fiducials/FID1>,                 # fiducial
            </Board/Mechanical/standoff_ain2700>,    # mechanical (no refdes — addressed by instanceId)
        ]
    }
}
```

## How to comply

- Author one `Registries` scope with `rel pcba:board:members` listing every placed component.
- Regenerate it with the component set; never hand-maintain it.
- Select subsets by `processClass`; do not author per-class registries.

### What the checker proves

`RegistriesChecker` is advisory. When components exist it warns if no `pcba:board:members`
relationship is authored anywhere on the stage, warns for each placed component missing from
the registry (under-inclusion), and warns for each target that is not a placed component
(stale or over-inclusive). It never fails the asset.

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Refdes Identity (CI.001)](/capabilities/pcb_aoi/component_identity/requirements/refdes-identity)
