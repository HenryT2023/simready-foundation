# Provenance

| Code | UO.015 |
|------|------|
| Validator | `ProvenanceChecker` |
| Applies to | board-root prim (discovered by its `pcba:board:*` attributes) |
| Requirement level | MUST |
| Tags | `provenance` |

## Summary

The board root MUST carry `pcba:board:generatorVersion` and `pcba:board:contentHash`, both
non-empty strings. Together they record which exporter produced the board and give a content
hash of the referenced assets for integrity verification.

This page follows PCBA to USD Input Contract **1.0.2**, section 11.

## Description

Every board needs a reproducible provenance trail:

- **`pcba:board:generatorVersion`** — the exporter / generator version that produced the board,
  so behaviour differences across versions can be traced.
- **`pcba:board:contentHash`** — a content hash of the referenced assets, letting a consumer
  verify the assets the board references are the ones expected.

Both are authored on the board-root prim alongside the rest of the `pcba:board:*` metadata
([UO.001](/capabilities/pcb_aoi/usd_organization/requirements/board-root)). A pending value may
be deferred with `pcba:prov:generatorVersion` / `pcba:prov:contentHash`.

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:board:generatorVersion` | `string` | MUST | Exporter / generator version that produced the board. |
| `pcba:board:contentHash` | `string` | MUST | Content hash of the referenced assets. |

## Why is it required?

- A generator version gives a trail from a board back to the tool that authored it.
- A content hash lets consumers verify referenced-asset integrity and detect drift.

## Example

```usda
def Xform "Board"
{
    string pcba:board:generatorVersion = "example_pcb_export 1.4.2"
    string pcba:board:contentHash = "sha256:0000…"
}
```

## How to comply

- Author both attributes on the board root and regenerate them on every export.

### What the checker proves

`ProvenanceChecker` fails when either attribute is absent from the board root (a matching
`pcba:prov:` marker downgrades this to a declared gap) or is declared but empty. It does not
verify the hash against the packaged files.

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
- [Board Root (UO.001)](/capabilities/pcb_aoi/usd_organization/requirements/board-root)
