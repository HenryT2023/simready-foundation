# Pin Count

| Code | CG.005 |
|------|------|
| Validator | `PinCountChecker` |
| Applies to | `placed component prim` |
| Requirement level | MUST (N/A for `fiducial` / `mechanical`) |
| Tags | `component`, `pins`, `contacts` |

## Summary

Every electrical component MUST carry `pcba:component:pinCount` (an integer, greater than
zero), and it MUST equal the number of pin prims on the component. It is the contact enumeration the
solder simulation relies on.

## Description

`pcba:component:pinCount` declares how many electrical contacts the component has.
The value MUST equal the number of pin prims authored on the component (the
`pkg_lead` meshes / pin `Xform`s under the component), so a validator can confirm
that the geometry and the declared count agree. A mismatch means the asset is
missing or has extra pin geometry, which would silently corrupt contact
enumeration.

The pipeline enumerates contacts from the pin prims to place and score solder
joints; `pinCount` is the cross-check that the enumeration is complete. For a
2-terminal passive this is `2`; for a QFN-48 it is `48`.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:pinCount` | `int` | MUST | Equals the number of pin prims on the component |

## Why is it required?

- Solder simulation enumerates every contact; a wrong or missing count silently
  drops or duplicates joints.
- A declared count that must equal the pin-prim count gives validators a cheap,
  unambiguous integrity check on the component's pin geometry.

## Example

```usda
def Xform "U7"
{
    int pcba:component:pinCount = 48

    def Scope "Pins"
    {
        # 48 pin prims (pkg_lead) — count MUST match pinCount
    }
}
```

## How to comply

- Set `pcba:component:pinCount` to the true number of contacts.
- Ensure the number of pin prims on the component equals `pinCount`.
- Do not count non-contact features (mounting tabs, thermal pads) unless they are
  authored as pin prims.
- `pinCount` counts pin *prims*; two pins sharing a `pcba:pin:number` do not surface here —
  see [CG.007](/capabilities/pcb_aoi/component_geometry/requirements/pin-geometry).

### What the checker proves

`PinCountChecker` runs on electrical components only. It fails an absent `pinCount` (a
`pcba:prov:pinCount` marker downgrades this to a declared gap) or a value not greater than zero.
When pin prims (those carrying `pcba:pin:number`) are found and their count differs from
`pinCount`, it **warns** rather than fails, because instancing can hide pins from a shared
prototype.

## For More Information

- [PCB Component Geometry](/capabilities/pcb_aoi/component_geometry/capability-component_geometry)
- [Pin Geometry (CG.007)](/capabilities/pcb_aoi/component_geometry/requirements/pin-geometry)
