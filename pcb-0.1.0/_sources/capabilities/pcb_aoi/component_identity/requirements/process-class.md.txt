# Process Class

| Code | CI.003 |
|------|------|
| Validator | `ProcessClassChecker` |
| Applies to | placed component prim (discovered by `pcba:component:*`) |
| Requirement level | MUST |
| Tags | `identity` |

## Summary

Every placed component prim MUST carry `pcba:component:processClass` — **how the part is
mounted** — from `SMT through_hole press_fit mechanical fiducial Mixed`. A `Mixed` part MUST
also list its real mount technologies in `pcba:component:processClasses`. Package families
(BGA, LGA, QFN, …) are not mount methods; they belong in `packageType`.

This page follows PCBA to USD Input Contract **1.0.2**, sections 8, 8.1 and 12.

## Description

There are only two real assembly methods — surface-mount and through-hole; `press_fit` is a
third mount style, and `mechanical` / `fiducial` are non-electrical placements. SMT and THT are
**one model with conditional fields**, not separate specs, and a single board routinely carries
both:

- **`SMT`** → `board_paste` deposits with the contact pair and `solderLayer`; per-contact pads;
  no holes.
- **`through_hole`** / **`press_fit`** → a `board_barrel` at every occupied joint carrying the
  hole data and the board-side association pair. Whether solder-defect classes apply is determined
  per pin by `pcba:pin:solderable`, not by the class
  ([CG.018](/capabilities/pcb_aoi/component_geometry/requirements/press-fit-state)).
- **`Mixed`** → the part combines technologies; `pcba:component:processClasses` (`token[]`)
  lists them, each from `{SMT, through_hole, press_fit}`.
- **`fiducial`** / **`mechanical`** → non-electrical placements with a reduced identity set: no
  pins, no BOM identity, no solder joint. They still MUST carry a valid `processClass`, `side`,
  and a role-bearing mesh.

A component MUST be discoverable by at least one of `refdes`, `instanceId`, or `processClass`;
deferring `processClass` with `pcba:prov:processClass = "not_yet_available"` is safe when
another is authored, and is preferred over guessing — a wrong class silently switches off
inspection classes a real part needs.

The superseded tokens `SMT_leaded`, `SMT_leadless`, and `BGA` are read and reported with a
warning naming the replacement (`SMT`).

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:component:processClass` | `token` | MUST | `SMT through_hole press_fit mechanical fiducial Mixed` — the mount method. |
| `pcba:component:processClasses` | `token[]` | MUST when `processClass = Mixed` | The real mount technologies combined, each in `{SMT, through_hole, press_fit}`. |

## Why is it required?

- The one-model design needs `processClass` to decide which conditional fields (paste vs
  barrels) apply to a part.
- Keeping package families out of this field keeps it a closed vocabulary a consumer can
  branch on; the open-ended package space lives in `packageType`.

## Example

```usda
def Xform "J1" (
    instanceable = true
    prepend references = @./protos/HDR2.usda@</Proto>
)
{
    string pcba:component:refdes = "J1"
    token  pcba:component:type = "connector"
    token  pcba:component:processClass = "through_hole"
}

def Xform "X9"
{
    string  pcba:component:refdes = "X9"
    token   pcba:component:processClass = "Mixed"
    token[] pcba:component:processClasses = ["through_hole", "SMT"]
}
```

## How to comply

- Author `pcba:component:processClass` on every placed component from the vocabulary; derive it
  from the footprint or an explicit classification when the source export lacks it.
- For `Mixed`, author `processClasses`.
- Put package families in `packageType`; put lead form in `pcba:pin:terminalType`.

### What the checker proves

`ProcessClassChecker` fails a component whose `processClass` is absent (a
`pcba:prov:processClass` marker downgrades this to a declared gap) or outside the vocabulary,
warns on a superseded token, and for `Mixed` fails a missing or invalid `processClasses` list.
It does not check that the class matches the part's actual geometry or pads.

## For More Information

- [PCB Component Identity](/capabilities/pcb_aoi/component_identity/capability-component_identity)
- [Press-Fit State (CG.018)](/capabilities/pcb_aoi/component_geometry/requirements/press-fit-state)
- [Package Type (CI.004)](/capabilities/pcb_aoi/component_identity/requirements/package-type)
