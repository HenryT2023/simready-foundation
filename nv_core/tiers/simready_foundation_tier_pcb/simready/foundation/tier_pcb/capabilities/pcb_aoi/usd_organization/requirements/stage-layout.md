# Stage Layout

| Code | UO.003 |
|------|------|
| Validator | `StageLayoutChecker` |
| Applies to | the board stage |
| Requirement level | MUST for a `board_substrate` mesh; the illustrated hierarchy is desirable, not required |
| Tags | `organization` |

## Summary

The board body MUST be present as a `Mesh` with `pcba:mesh:role = "board_substrate"`. Beyond
that, the contract describes a **desirable** stage shape — layers grouped by side, components,
copper, paste, holes, registries — but does not mandate it: an exporter that satisfies every
requirement with a different arrangement is conformant. Discovery is by role and attribute,
never by prim name.

This page follows PCBA to USD Input Contract **1.0.2**, section 3.

## Description

Prim names below are illustrative. A consumer finds geometry by `pcba:mesh:role`, the board
root by `pcba:board:*`, components by `pcba:component:*`, and the component index by the
`pcba:board:members` registry — never by walking a fixed path.

The desirable structure (the **shape** matters, not the names):

```text
/<AssetName>                 Xform   default prim; carries pcba:board:* root metadata
├── Looks/                   Scope   materials, one per role class
├── Substrate                Mesh    board_substrate — a solid slab of real thickness
├── Layers/                  Scope   stackup grouping; descriptive pcba:layer:* only, NOT a side source
│   ├── Top/                 Scope   Components/<refdes> · Copper/ (board_pad) · Paste/ (board_paste)
│   ├── Inner/               Scope   reserved; MAY be empty or absent
│   └── Bottom/              Scope   same shape as Top/ — boards are populated on both sides
├── Fiducials/<refdes>       Xform   fiducials & mechanical parts — reduced identity set
├── Holes/                   Scope   board_barrel per occupied THT joint (incl. press_fit);
│                                    board_hole prims optional
└── Registries/Components    Scope   rel pcba:board:members → every placed component (SHOULD)

proto/<package>.usda         component prototype, authored once, instanced per placement
```

Nesting under `Layers/Top` vs `Layers/Bottom` is organization only: a component's side comes
from `pcba:component:side`, a mesh's from its role. The one sanctioned layer derivation is
paste `solderLayer` from an ancestor `pcba:layer:side`
([BG.008](/capabilities/pcb_aoi/board_geometry/requirements/paste-side)).

A **panel** is a layer above the single board: it places the board master once per position
(`pcba:panel:boards` → every board instance; each instance `pcba:board:prototype` → the master),
positions may be rotated, and board geometry is never duplicated.

## Fields

| Attribute | On | Type | Req | Notes |
|-----------|----|------|-----|-------|
| `pcba:mesh:role = "board_substrate"` | the board body `Mesh` | `token` | MUST | Exactly the substrate slab; the pipeline needs a body to seat holes and layers against. |
| `pcba:panel:boards` | panel root | `rel` | SHOULD (panels) | Every board instance on the panel. |
| `pcba:board:prototype` | each board instance | `rel` | SHOULD (panels) | The master this position instances. |

## Why is it required?

- Without a substrate body there is nothing for holes to pass through and no faces for layers
  to sit on.
- Leaving the hierarchy free lets any exporter emit its natural structure while consumers stay
  interoperable through roles and attributes.

## Example

```usda
def Xform "Board"
{
    float pcba:board:thicknessMm = 1.6

    def Mesh "Substrate"
    {
        token pcba:mesh:role = "board_substrate"
    }

    def Scope "Layers"
    {
        def Scope "Top"
        {
            token pcba:layer:side = "top"               # descriptive only
            def Scope "Components"
            {
                def Xform "R12" (
                    instanceable = true
                    prepend references = @./protos/0402.usda@</Proto>
                ) {}
            }
            def Scope "Copper" {}
            def Scope "Paste" {}
        }
        def Scope "Bottom"
        {
            token pcba:layer:side = "bottom"
        }
    }
    def Scope "Holes" {}
    def Scope "Registries"
    {
        def Scope "Components" {}
    }
}
```

## How to comply

- Author the board body as a `Mesh` with `pcba:mesh:role = "board_substrate"`.
- Follow the desirable shape where convenient; rely on roles and `pcba:*` attributes — not
  names — for anything a consumer must find.
- For a panel, reference the board master per position and author the two panel rels.

### What the checker proves

`StageLayoutChecker` fails only when no `Mesh` on the stage carries role `board_substrate`. It
does not check for any group, scope, or name, and it does not check the panel relationships.
(There is no "THT components but no `board_hole`" check here; barrels are BG.003.)

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Board Root (UO.001)](/capabilities/pcb_aoi/usd_organization/requirements/board-root)
- [Registries (UO.008)](/capabilities/pcb_aoi/usd_organization/requirements/registries)
