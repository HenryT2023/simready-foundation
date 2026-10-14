# PCB Component Geometry

## Overview

This capability defines the **geometric and appearance ground truth** carried on every placed
PCB component and on its pins and meshes. It realizes the *Component Geometry (CG)* codes of the
PCBA to USD Input Contract **1.0.2** (section 7 components, 8 component attributes, 9 mesh
roles and material class, 10 pins): the data a board-asset author must supply so an AOI
synthetic-data pipeline can place a component correctly, enumerate its contacts, reason about
its height and orientation, and inject appearance / orientation / polarity defects against a
known-good reference.

It covers five families of ground truth:

- **Placement** — board side, nominal board-local position, and rotation about the board
  normal (`pcba:component:side`, `…:nominalPosMm`, `…:nominalRotationDeg`), plus the **anchor**
  convention (`pcba:component:anchor`, `…:bodyCentroidLocal`, `pcba:mesh:originOffset` on the
  body mesh) that makes placement deterministic when the mesh origin sits off the body.
- **Body dimensions** — component height (`heightMm`); a body-mesh `extent` is recommended so
  world bounds and geometric cross-checks are computable.
- **Pins** — pin count, pin pitch, and per-pin contact data (`pcba:pin:number` unique within
  the part, `…:solderable` as the per-pin solder authority, optional `…:crossSection`,
  `…:terminalType`, `…:designator`), plus the actual pin-1 position for orientation-sensitive
  parts. Each body, lead, and marking is its **own prim**; a merged lump cannot be defected or
  associated. Boards do not have pins: a board site names a pin with
  `pcba:board:componentPinNumber`.
- **Markings & polarity** — polarity type and visible markings; when a part carries a pin-1 or
  polarity marker it is **standalone geometry** (`pcba:mesh:role = pkg_marking`), never baked
  into a texture.
- **Appearance & material** — nominal (representative, not photoreal) body colour, finish, and
  material class on the component, and `pcba:mesh:matClass` authored on `pkg_*` / `fixture_*`
  meshes (derived from the role on `board_*`).

Real geometry is required for final training data; boxes standing in for parts are not
acceptable, and a dimensionally correct outline extrusion is provisional only. Fiducial and
mechanical placements carry a reduced set: `side` MUST, pose and appearance SHOULD, pin and
identity fields Not Applicable.

## Requirements

| Code | Requirement | Summary |
|------|-------------|---------|
| CG.001 | [Placement](/capabilities/pcb_aoi/component_geometry/requirements/placement) | `side` on every placement; board-local nominal position (mm) and rotation about Z on electrical parts. |
| CG.002 | [Anchor & Geometry Reference](/capabilities/pcb_aoi/component_geometry/requirements/anchor) | Declared anchor; `bodyCentroidLocal` on the part and `originOffset` on the body mesh give deterministic placement when the mesh origin is off-body. |
| CG.003 | [Body Height](/capabilities/pcb_aoi/component_geometry/requirements/body-height) | `heightMm` > 0 (Z extent); a body-mesh `extent` is recommended. |
| CG.005 | [Pin Count](/capabilities/pcb_aoi/component_geometry/requirements/pin-count) | `pcba:component:pinCount` equals the number of pin prims. |
| CG.006 | [Pin Pitch](/capabilities/pcb_aoi/component_geometry/requirements/pin-pitch) | CONDITIONAL: contact spacing in mm when meaningful; omitted for 2-terminal passives. |
| CG.007 | [Pin Geometry](/capabilities/pcb_aoi/component_geometry/requirements/pin-geometry) | Per-pin `number` (unique within the part) and `solderable` (bool); `crossSection`, `terminalType`, `designator` optional. |
| CG.008 | [Pin-1 Position](/capabilities/pcb_aoi/component_geometry/requirements/pin1-position) | CONDITIONAL: actual pin-1 offset from the anchor for keyed / orientation-sensitive parts. |
| CG.009 | [Polarity](/capabilities/pcb_aoi/component_geometry/requirements/polarity) | CONDITIONAL: polarity type for polarized parts; an existing marker is standalone `pkg_marking` geometry. |
| CG.010 | [Markings](/capabilities/pcb_aoi/component_geometry/requirements/markings) | CONDITIONAL: visible marking text for OCR / wrong-part ground truth. |
| CG.011 | [Nominal Appearance](/capabilities/pcb_aoi/component_geometry/requirements/nominal-appearance) | Representative body colour, finish, and material class on the component. |
| CG.012 | [Per-Surface Material](/capabilities/pcb_aoi/component_geometry/requirements/per-surface-material) | `matClass` authored on `pkg_*` / `fixture_*` meshes; derived from the role on `board_*`. |
| CG.018 | [Press-Fit State](/capabilities/pcb_aoi/component_geometry/requirements/press-fit-state) | Press-fit joints still get barrels; solder-defect applicability is determined per pin by `solderable`. No executable rule. |

```{toctree}
:maxdepth: 1
:hidden:

requirements
requirements/placement
requirements/anchor
requirements/body-height
requirements/pin-count
requirements/pin-pitch
requirements/pin-geometry
requirements/pin1-position
requirements/polarity
requirements/markings
requirements/nominal-appearance
requirements/per-surface-material
requirements/press-fit-state
```
