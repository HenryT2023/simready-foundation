# Requirements

## Summary

Levels follow PCBA to USD Input Contract **1.0.2**. Fields marked N/A are not authored on
`fiducial` / `mechanical` placements.

- Each electrical component **MUST** carry `pcba:component:refdes`, unique within one board;
  fiducial / mechanical parts **SHOULD**, and otherwise **MUST** carry `instanceId`. A placement
  is discovered by any of `refdes`, `instanceId`, `processClass` — never by prim name (CI.001).
- Electrical parts **MUST** author `pcba:component:type` from its vocabulary, not derived from
  the refdes (CI.002).
- Every placement **MUST** author `pcba:component:processClass` — the mount method — from
  `SMT through_hole press_fit mechanical fiducial Mixed`; `Mixed` **MUST** list
  `processClasses` (CI.003).
- Electrical parts **SHOULD** author `pcba:component:packageType`, a string identifying a
  specific body; omit and declare the gap rather than use a family word (CI.004).
- Electrical parts **MUST** provide `pcba:component:footprintId`, with
  `pcba:component:sourceOrigin` when the id is source-specific (CI.005).
- Part identity is **CONDITIONAL**: `mpn` / `manufacturer` and `value` / `tolerance` are two
  independent groups, plus `customerPartNumber`; author when known, never invent (CI.006).
- The per-component manifest is realized **without a sidecar** — the instance attributes plus
  the prototype `reference` are that record (CI.007; no executable rule).

## Requirements

```{requirements-table}
```

```{toctree}
:maxdepth: 1
:hidden:

requirements/refdes-identity
requirements/component-type
requirements/process-class
requirements/package-type
requirements/footprint-id
requirements/part-identity
requirements/component-manifest
```
