# Refdes Identity

| Code | CI.001 |
|------|------|
| Validator | `RefdesChecker` |
| Applies to | placed component prim (discovered by `pcba:component:*`) |
| Requirement level | MUST for electrical parts; SHOULD for `fiducial` / `mechanical` (then `instanceId` MUST) |
| Tags | `identity` |

## Summary

Every electrical component MUST carry `pcba:component:refdes`, the reference designator, unique
**within one board**. `fiducial` and `mechanical` placements SHOULD carry one; when they do not,
they MUST carry `pcba:component:instanceId` so the placement stays addressable. A placed
component MUST be discoverable by at least one of `refdes`, `instanceId`, or `processClass` —
never by prim name.

This page follows PCBA to USD Input Contract **1.0.2**, sections 3, 8 and 8.1.

## Description

The reference designator (`U7`, `C12`) is the canonical identity of a placed part and the key
every board-side association uses (`pcba:board:refdes` + `componentPinNumber`,
[BG.012](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)). It is unique per
**board**, not per panel: a panel repeats the same refdes at every position because it is the
same board, and a position's sites resolve against that position's board. Address a specific
placement on a panel by prim path or `instanceId`, never by refdes alone.

Not every placement has a refdes. Mounting hardware routinely ships without one (in CAD it is
often just a symbol name) and fiducials usually but not always carry one. For these two
non-electrical classes `refdes` is SHOULD, and `instanceId` provides identity when it is absent.
Consumers look for any of the three discovery attributes; an exporter that omits all three
produces a part no consumer can see.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:refdes` | `string` | MUST (electrical); SHOULD (fiducial / mechanical) | Reference designator, unique within one board. |
| `pcba:component:instanceId` | `string` | MUST when `refdes` is absent | Stable per-placement id. |

## Why is it required?

- Every board-side association and registry entry resolves through the refdes.
- Discovery by attribute, not prim name, is what lets any exporter's hierarchy interoperate.
- Requiring an `instanceId` fallback keeps refdes-less hardware addressable without inventing
  designators.

## Example

```usda
def Xform "U7" ( instanceable = true; prepend references = @./protos/QFN8.usda@</Proto> )
{
    string pcba:component:refdes = "U7"
}

def Xform "standoff_1"
{
    string pcba:component:instanceId = "MECH-M1-standoff"   # no refdes: still addressable
    token  pcba:component:processClass = "mechanical"
    token  pcba:component:side = "top"
}
```

## How to comply

- Author `pcba:component:refdes` on every electrical part, unique within the board.
- Author `refdes` where available on fiducials and mechanical parts; otherwise author
  `instanceId`.
- Rely on the attributes, not prim names, for discovery and association.

### What the checker proves

`RefdesChecker` fails an electrical component with no non-empty `refdes` (a `pcba:prov:refdes`
marker downgrades this to a declared gap), fails a fiducial or mechanical placement with neither
`refdes` nor `instanceId`, fails duplicate refdes values among the board's authored components
(instance copies are deduplicated, so a panel is not flagged), and fails a stage with no
components at all.

## For More Information

- [PCB Component Identity](/capabilities/pcb_aoi/component_identity/capability-component_identity)
- [Registries (UO.008)](/capabilities/pcb_aoi/usd_organization/requirements/registries)
