# Paste Side

| Code | BG.008 |
|------|------|
| Validator | `PasteSideChecker` |
| Applies to | `board_paste` prim (mesh role `board_paste`) |
| Requirement level | MUST when paste is supplied — or derivable from the containing layer's `pcba:layer:side` |
| Tags | `board`, `paste`, `side` |

## Summary

When solder paste geometry is supplied, the side of each `board_paste` deposit MUST be
determinable: either `pcba:board:solderLayer` (`top` \| `bottom`) is authored on the deposit,
or it derives from a containing layer prim's `pcba:layer:side`.

This page follows PCBA to USD Input Contract **1.0.2**, sections 10 and 11.1.

## Description

A paste deposit sits on one face of the board. `pcba:board:solderLayer` records that face so
the pipeline places the reflowed joint on the correct side and routes the deposit to the
matching top/bottom process stage.

The contract allows **one** side derivation from layer organization: paste deposits are
normally grouped under side-named paste layers, so when `solderLayer` is not authored per
deposit the containing layer prim's `pcba:layer:side` is an unambiguous source. This is the
only sanctioned use of `pcba:layer:side` — a component's or a general mesh's side comes from
`pcba:component:side` / `pcba:mesh:role`, never from the layer it sits under.

This is a conditional MUST: it applies only when paste geometry is present. The contact
association is separate and is not relaxed — see
[Paste Association (BG.007)](/capabilities/pcb_aoi/board_geometry/requirements/paste-association).

## Fields

| Attribute | On | Type | Req | Notes |
|-----------|----|------|-----|-------|
| `pcba:board:solderLayer` | `board_paste` | `token` | MUST when paste supplied — or derivable | `top` \| `bottom`. |
| `pcba:layer:side` | an ancestor layer prim | `token` | the derivable alternative | Optional descriptive layer metadata; sanctioned as a side source for paste only. |

## Why is it required?

- Solder generation must place the reflowed joint on the correct board face.
- Top vs bottom selects the matching process stage and defect context.
- Allowing the layer derivation matches how exporters already group paste, without
  inventing a per-deposit attribute.

## Example

```usda
def Scope "Top"
{
    token pcba:layer:side = "top"    # would satisfy BG.008 for children by derivation

    def Scope "Paste"
    {
        def Mesh "paste_U7_1"
        {
            token  pcba:mesh:role = "board_paste"
            token  pcba:mesh:matClass = "solder"
            token  pcba:board:solderLayer = "top"      # authored explicitly here
            string pcba:board:refdes = "U7"
            string pcba:board:componentPinNumber = "1"
        }
    }
}
```

## How to comply

- Author `pcba:board:solderLayer` on each supplied `board_paste` deposit, or group deposits
  under a layer prim carrying `pcba:layer:side`.
- Use only `top` or `bottom`; take the value from the source paste layer.

### What the checker proves

`PasteSideChecker` fails a `board_paste` whose authored `solderLayer` is outside the vocabulary,
and fails one with no `solderLayer` and no ancestor `pcba:layer:side`. It does not verify that
the stated side matches the deposit's geometric position.

## For More Information

- [PCB Board Geometry](/capabilities/pcb_aoi/board_geometry/capability-board_geometry)
- [Paste Association (BG.007)](/capabilities/pcb_aoi/board_geometry/requirements/paste-association)
