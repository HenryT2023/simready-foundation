# Packaging Relative

| Code | UO.012 |
|------|------|
| Validator | `RelativeReferencesChecker` |
| Applies to | every `references` / `payloads` arc in the board package |
| Requirement level | MUST |
| Tags | `packaging` |

## Summary

All `references` and `payloads` MUST use **relative** asset paths and nothing may point outside
the package. The board is **one asset, placed — never duplicated**: a panel references the board
once per position, and every repeated component references a shared prototype with
`instanceable = true`.

This page follows PCBA to USD Input Contract **1.0.2**, section 4.

## Description

The rule in one sentence: **author each thing once, then place it as many times as it occurs.**

- **Relative and self-contained.** Absolute filesystem paths, drive letters, and URLs break
  when the package is moved or mirrored. Inventory the packaged files in
  `pcba:board:packageManifest` ([UO.013](/capabilities/pcb_aoi/usd_organization/requirements/package-manifest)).
- **One board asset, placed.** A panel does not contain a second copy of the board geometry;
  it points at the board master once per position, each with its own transform. Do not ship
  the same geometry embedded in both a board file and a panel file.
- **Place every repeated component, don't re-author it.** Parts sharing a package + geometry
  point at one prototype (`references` + `instanceable = true`). THT pin↔hole links are
  authored **board-side** on the `board_barrel` / `board_pad`
  ([BG.012](/capabilities/pcb_aoi/board_geometry/requirements/hole-occupancy)) so components
  stay instanceable.
- **Breakaway rails / edge tabs** that are genuinely part of the fabricated board are board
  geometry.

Payloading heavy groups so a consumer can defer-load is good practice but is not a contract
requirement.

## Fields

| Rule | Req | Notes |
|------|-----|-------|
| Relative asset paths | MUST | Every `references` / `payloads` assetPath is relative; nothing points outside the package. |
| One board asset | MUST | A panel references the board master per position; geometry is never duplicated. |
| Shared prototypes | MUST | Repeated parts reference one prototype with `instanceable = true`; associations stay board-side. |

## Why is it required?

- Relative, self-contained packaging lets the board be moved, mirrored, and re-published
  without rewriting paths.
- One prototype per package and one board master per panel keep the stage light and make the
  pipeline treat identical parts as one shape.

## Example

```usda
def Xform "U7" (
    instanceable = true
    prepend references = @./protos/QFN8.usda@</Proto>
)
{
    string pcba:component:refdes = "U7"
}

# Panel: the board master placed per position, never copied
def Xform "Position_2" (
    instanceable = true
    prepend references = @./board.usda@</Board>
)
{
    rel pcba:board:prototype = </Panel/_class_Boards/Board>
}
```

## How to comply

- Use relative asset paths for every reference and payload; keep all files inside the package
  and list them in the manifest.
- Reference one shared prototype per package + geometry and set `instanceable = true`.
- On a panel, reference the board master per position; never embed a second copy.

### What the checker proves

`RelativeReferencesChecker` fails any prim whose `references` or `payloads` assetPath is
absolute — a leading `/`, a drive letter, or a URL scheme. It also reports each distinct stage
composition error as a failure, including unresolved references and payloads. It does not verify that successfully resolved targets
stay inside the package, that repeated parts share a prototype, that `instanceable` is set,
or that a panel avoids duplicating board geometry.

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Package Manifest (UO.013)](/capabilities/pcb_aoi/usd_organization/requirements/package-manifest)
