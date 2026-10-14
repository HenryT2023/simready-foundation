# Requirements

## Summary

Levels follow PCBA to USD Input Contract **1.0.2**. Fields marked N/A are not authored on
`fiducial` / `mechanical` placements; their pose and appearance fields are SHOULD.

- **Placement (CG.001)** — every placement MUST carry `pcba:component:side`; electrical parts
  MUST also carry `pcba:component:nominalPosMm` (board-local x, y in mm) and
  `pcba:component:nominalRotationDeg` (about the board normal Z).
- **Anchor (CG.002)** — the asset root MUST sit at a declared `pcba:component:anchor`;
  `pcba:component:bodyCentroidLocal` on the part and `pcba:mesh:originOffset` on the body mesh
  make placement deterministic when the mesh origin is off-body.
- **Body height (CG.003)** — `pcba:component:heightMm` MUST be authored and greater than zero; a
  standard USD `extent` on the body mesh is recommended.
- **Pins (CG.005–CG.008)** — `pcba:component:pinCount` MUST equal the number of pin prims;
  `pcba:component:pinPitchMm` is CONDITIONAL (when meaningful); each pin prim MUST carry
  `pcba:pin:number` (unique within the part) and `pcba:pin:solderable` (bool), with
  `crossSection` / `terminalType` / `designator` OPTIONAL; `pcba:component:pin1PosMm` is
  CONDITIONAL for keyed / orientation-sensitive parts. Boards have no pins: a board site names a
  pin with `pcba:board:componentPinNumber`.
- **Polarity & markings (CG.009, CG.010)** — `pcba:component:polarityType` is CONDITIONAL for
  polarized parts and `pcba:component:markings` when markings are present; where a pin-1 /
  polarity marker exists it is **standalone geometry** (`pkg_marking`), never baked into a
  texture.
- **Appearance & material (CG.011, CG.012)** — electrical parts MUST carry representative
  `bodyColorNominal`, `finishNominal`, and `materialClassNominal`; `pcba:mesh:matClass` MUST be
  authored on `pkg_*` / `fixture_*` meshes and derives from the role on `board_*`.
- **Press-fit state (CG.018)** — press-fit joints are described like any THT joint (barrel +
  association); solder-defect applicability is determined per pin by `pcba:pin:solderable`. No
  executable rule.

## Requirements

```{requirements-table}
```

```{toctree}
:maxdepth: 1
:hidden:

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
