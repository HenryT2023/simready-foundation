# Package Manifest

| Code | UO.013 |
|------|------|
| Validator | `PackageManifestChecker` |
| Applies to | board-root prim (distributed package) |
| Requirement level | MUST for a distributed package |
| Tags | `packaging` |

## Summary

A distributed board package MUST author `pcba:board:packageManifest` (an `asset`) on
the board-root prim — an inventory of the packaged files. This is the **package-file
BOM**, distinct from the CI.007 component manifest.

## Description

When the board is distributed as a package, consumers need to know which files the
package contains and how to verify them. `pcba:board:packageManifest` points at that
inventory: for each packaged file, its **relative path**, **size**, **format
version**, and an **optional hash**.

This is a **package-file** inventory — the list of what is in the package. It is
**distinct from the CI.007 component manifest**, which is a per-`refdes` record of BOM
identity, footprint, and component asset ID realized as distributed per-prim
attributes. The package manifest describes the package's files; the component manifest
describes the board's components.

The manifest is a converter-authored, **Easy** field. It is required for a distributed
package; a stage that is not being packaged for distribution need not carry it.

The board root is discovered by its `pcba:board:*` metadata. It need not be named
`/Board` or be the stage's default prim. When the manifest is pending, omit the
asset attribute and author `string pcba:prov:packageManifest = "not_yet_available"`
on that board root (or `"source_data_required"` after unsuccessful sourcing).

### Validation coverage

`PackageManifestChecker` cannot determine whether this is a distributed package.
An absent manifest without a marker therefore produces a WARNING; a deferred
manifest produces an INFO declared gap. An authored manifest satisfies this
checker's presence check. It does not read the inventory or verify its path,
file sizes, versions, or hashes. Those are separate packaging checks.
The reporting limitation is described in the
[PCB-Assembly guide](/profiles/pcb_assembly).

## Fields

| Attribute | Type | Req | Notes |
|-----------|------|-----|-------|
| `pcba:board:packageManifest` | `asset` | MUST for a distributed package | Inventory of packaged files: relative path, size, format version, optional hash. Distinct from the CI.007 component manifest. |

## Why is it required?

- A distributed package needs a self-contained inventory so consumers can enumerate
  and verify its files without inspecting the filesystem.
- Keeping the package-file BOM distinct from the component manifest avoids conflating
  "what files ship" with "what components exist."

## Example

```usda
def Xform "Board"
{
    asset pcba:board:packageManifest = @./package_manifest.json@
}
```

```json
{
  "files": [
    { "path": "board.usda",           "size": 128144, "formatVersion": "1.0", "hash": "blake3:1a2b…" },
    { "path": "proto/0402.usda",      "size":   9021, "formatVersion": "1.0" },
    { "path": "package_manifest.json","size":    412, "formatVersion": "1.0" }
  ]
}
```

## How to comply

- Author `pcba:board:packageManifest` on the board-root prim for any distributed package.
- Populate the manifest with one entry per packaged file: relative path, size, format
  version, and (optionally) a hash.
- Keep it separate from the CI.007 component manifest — they answer different
  questions.
