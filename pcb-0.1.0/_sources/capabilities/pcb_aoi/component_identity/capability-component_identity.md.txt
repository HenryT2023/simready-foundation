# PCB Component Identity

## Overview

This capability defines the **identity and BOM fields authored on each placed component prim**
of a PCB board USD. It realizes the *Common Identifiers (CI)* codes of the PCBA to USD Input
Contract **1.0.2** (section 8 component identity, 8.1 fiducials and mechanical parts).

Every placed component — an `Xform` that references a shared prototype and is discovered by its
`pcba:component:*` attributes, never by prim name or path — carries a uniform set of fields
describing what the part *is*: its reference designator (or `instanceId`), component type,
mount method (`processClass`), package and footprint, and its part identity. These are the
ground truth a defect-simulation pipeline uses to find components, select the SMT / THT
conditionals that apply, and label wrong-part / wrong-value defects. The board follows one
uniform component model — SMT and THT are conditional fields keyed off `processClass`, not
separate asset classes.

**Fiducials and mechanical parts** (`processClass = fiducial` / `mechanical`) are non-electrical
placements with a **reduced identity set**: `refdes` or `instanceId`, `processClass`, `side`, and
a role-bearing mesh. The electrical / BOM / pin fields (`type`, `packageType`, `footprintId`,
`sourceOrigin`, `mpn`, `manufacturer`, `value`, `tolerance`, `customerPartNumber`, `pinCount`,
`pinPitchMm`, `polarityType`, `pin1PosMm`, `markings`) are Not Applicable to them and validators
do not demand them.

The final requirement (CI.007) is the **component manifest**: one record per placed component
linking identity, footprint, and component asset — realized without a sidecar from the
per-prim attributes plus the prototype reference.

## Summary

- **Identity fields on every placed component**, under `pcba:component:*`.
- **`refdes` is unique within one board** (it repeats across panel positions); `instanceId`
  stands in for refdes-less hardware.
- **`type` and `processClass` classify the part** from closed vocabularies; `packageType`
  (SHOULD) identifies a specific physical body as a free string.
- **`footprintId` (plus `sourceOrigin` when source-specific)** points at the footprint in the
  source library and says how far to trust it.
- **Part identity is CONDITIONAL** — `mpn` / `manufacturer` and `value` / `tolerance` are two
  independent groups; author when known, never invent.
- **The component manifest is distributed on the stage**, not a sidecar.

## Applies to

A placed component prim: an `Xform` carrying `pcba:component:*` attributes (at least one of
`refdes`, `instanceId`, `processClass`) and, for electrical parts, referencing a shared
prototype. The same fields apply uniformly to SMT and THT parts.

## Requirements

| Code | Requirement | Summary |
|------|-------------|---------|
| CI.001 | [refdes-identity](/capabilities/pcb_aoi/component_identity/requirements/refdes-identity) | `pcba:component:refdes` MUST on electrical parts, unique within one board; SHOULD on fiducial / mechanical, which then carry `instanceId`. |
| CI.002 | [component-type](/capabilities/pcb_aoi/component_identity/requirements/component-type) | `pcba:component:type` token from a fixed vocabulary; classified, not derived from `refdes`. |
| CI.003 | [process-class](/capabilities/pcb_aoi/component_identity/requirements/process-class) | `pcba:component:processClass` = how the part is mounted (`SMT through_hole press_fit mechanical fiducial Mixed`); `Mixed` lists `processClasses`. |
| CI.004 | [package-type](/capabilities/pcb_aoi/component_identity/requirements/package-type) | SHOULD: `pcba:component:packageType` string identifying a specific body (standard or manufacturer designation), never a family word. |
| CI.005 | [footprint-id](/capabilities/pcb_aoi/component_identity/requirements/footprint-id) | `pcba:component:footprintId` identifies the footprint in the source library; `sourceOrigin` states its trust when source-specific. |
| CI.006 | [part-identity](/capabilities/pcb_aoi/component_identity/requirements/part-identity) | CONDITIONAL: `mpn` / `manufacturer`, `value` / `tolerance`, `customerPartNumber` — authored when known, never invented. |
| CI.007 | [component-manifest](/capabilities/pcb_aoi/component_identity/requirements/component-manifest) | One record per placed component — per-prim attributes plus the prototype reference; no sidecar. No executable rule. |

```{toctree}
:maxdepth: 1
:hidden:

requirements
requirements/refdes-identity
requirements/component-type
requirements/process-class
requirements/package-type
requirements/footprint-id
requirements/part-identity
requirements/component-manifest
```
