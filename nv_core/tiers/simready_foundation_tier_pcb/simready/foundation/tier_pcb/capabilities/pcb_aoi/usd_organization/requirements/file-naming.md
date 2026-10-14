# File Naming

| Code | UO.016 |
|------|------|
| Validator | `FileNamingChecker` |
| Applies to | The board USD layer file and every referenced / payloaded / sublayered file |
| Requirement level | SHOULD |
| Tags | `packaging`, `portability`, `naming` |

## Summary

Asset file names SHOULD be clean ASCII with no spaces and no parentheses, so USD asset references
and downstream tooling resolve reliably across platforms. (Prim and attribute names must be valid
identifiers regardless.)

This page follows PCBA to USD Input Contract **1.0.2**, section 2.

## Description

USD asset paths containing spaces or parentheses break reference resolution and the shells, URL
encoders, and path globs that consume the package. Emit file names using ASCII letters, digits,
`-`, `_`, and `.` — no whitespace, no `(` / `)`. The rule applies to the board layer file and to
every file it references.

## Fields

This requirement constrains file names, not USD attributes; there are no attributes to author.

## Why is it required?

- Spaces and parentheses in asset paths break USD reference resolution.
- Clean ASCII names survive shells, URL encoding, and cross-platform path handling.
- Reliable resolution is a prerequisite for the relative, self-contained packaging required by
  [UO.012](/capabilities/pcb_aoi/usd_organization/requirements/packaging-relative).

## Example

```text
# Non-conformant
My Board (Rev A).usda

# Conformant
MyBoard_RevA.usda
```

## How to comply

- Name the board layer file and every referenced file using ASCII letters, digits, `-`, `_`,
  and `.` only; replace spaces with `_` or `-`.
- Keep names stable so relative references stay valid across the package.

### What the checker proves

`FileNamingChecker` is advisory: it warns once per distinct file name among the stage's used
layers that contains a space, a parenthesis, or a non-ASCII character. It does not check prim or
attribute names.

## For More Information

- [PCB USD Organization](/capabilities/pcb_aoi/usd_organization/capability-usd_organization)
