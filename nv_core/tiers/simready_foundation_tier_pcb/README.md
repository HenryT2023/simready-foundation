# simready-foundation-tier-pcb

SimReady Foundation **PCB tier**: the PCB/PCBA AOI validation content as a
separately publishable tier wheel — capabilities (requirements + validator
rules), features, and profiles for the **PCB → USD contract**, which defines the
stage structure, geometry, and `pcba:*` metadata a printed circuit board or a
populated assembly (PCBA) must carry as a USD asset. The profiles describe assets,
not pipeline stages: they apply whatever produced the file. The motivating
consumer is the AOI synthetic-data pipeline.

## Contents

- `simready/foundation/tier_pcb/capabilities/pcb_aoi/` — the `pcb_aoi`
  capability tree: requirement markdown plus `validation.py` rule modules for
  board geometry (`BG.*`), component geometry (`CG.*`), component identity
  (`CI.*`), and USD organization (`UO.*`).
- `simready/foundation/tier_pcb/features/` — six features cut along the export workflow:
  `FET_211_STANDARD` (component identity), `FET_212_STANDARD` (component geometry),
  `FET_213_STANDARD` (board geometry), `FET_214_STANDARD` (USD core), `FET_215_STANDARD`
  (AOI appearance), `FET_216_STANDARD` (delivery package).
- `simready/foundation/tier_pcb/profiles/` — two profiles: `PCB-Assembly` (a populated
  circuit board assembly; all six features) and `PCB-Board` (the board on its own: the four
  features that do not concern placed components).

## Usage

This tier requires a **tier-aware `simready-validate` (2026.8 or later)** together with
`usd-validation-nvidia` 1.21 or later and Python 3.10–3.12; earlier `simready-validate` releases
either cannot discover tiers or (2026.7.1) hard-pin `usd-validation-nvidia` 1.20.0. Install the
validator with the repository's root `requirements.txt`, which resolves a compatible build, then
build and install the tier wheels:

```bash
python -m pip install -r requirements.txt
python nv_core/tiers/_tooling/build_tiers.py
python -m pip install nv_core/tiers/_build/dist/simready_foundation_tier_core-*.whl nv_core/tiers/_build/dist/simready_foundation_tier_pcb-*.whl
simready-validate --profile PCB-Assembly --version 0.1.0 board.usda -v
```

Run these commands from the Foundation repository root in your virtual environment. Building
requires `uv` on `PATH` and the build dependencies described in
`nv_core/tiers/_tooling/README.md`. Reinstalling a rebuilt wheel at the same version requires
`--force-reinstall --no-deps`. The PCB wheel is an alpha artifact built locally; it is not yet
published to a package index.

Discovery is via the standard tier entry points (`usd_validation_nvidia` and
`simready.tier`); no path flags are required once the wheel is installed.
Select `--profile PCB-Assembly --version 0.1.0` explicitly unless the asset has
`customLayerData.SimReady_Metadata.validation` profile metadata. The CLI does not
infer this profile from `pcba:*` attributes.

## Contract and reporting scope

The current wheel `0.1.0a1` and profiles `PCB-Assembly@0.1.0` and `PCB-Board@0.1.0`
implement the **PCB to USD input contract v1.0.2**. The contract document and its reference
validator are published with the contract release; this tier is the SimReady packaging of that
validator. Wheel, profile and contract carry independent version numbers — the contract's
version is not the `--version` argument.

`simready-validate` (checked through 2026.8.0rc3) returns blocking and non-blocking failures but
filters out INFO declared gaps and WARNING advisories. A PASS therefore means no
reported failure; it does not prove that no declared gaps remain. The contract's
reference validator reports all three buckets (failures, declared gaps, warnings)
when a complete report is needed. The tier does not provide a replacement
reporting engine.

## Tests

After building and installing the current wheel:

```bash
python -m pip install pytest
python -m pytest nv_core/tiers/simready_foundation_tier_pcb/tests/ -q
python build_docs.py
```

The USD fixtures live in `sample_content/pcb/` at the repo root (shared sample content, not
under the tier) and are tracked with Git LFS. Run `git lfs pull` if a fixture starts
with `version https://git-lfs.github.com/spec/v1` instead of `#usda 1.0`.
The fixtures carry no renderable geometry: they illustrate the metadata contract and are not a
render or runtime acceptance test. Every test works on a scratch copy; the fixtures are never
modified.

- `sample_content/pcb/board_min.usda` — the conformant reference board. Validated through the
  `PCB-Assembly` profile (expected: PASS, zero blocking issues) and used as the base for every
  mutation: the negative matrix (expected: exactly the rule for the mutated requirement fires, at
  the stated severity) and the composition scenarios (expected: the named rule fires, or the panel
  passes).
- `sample_content/pcb/board_bad_role.usda` — `board_min` with one pad role set to `board_bogus`. Validated
  through the profile (expected: FAIL with exactly one UO.009).
- `sample_content/pcb/protos/QFN8.usda`, `sample_content/pcb/protos/HDR2.usda` — the component prototypes `board_min`
  references; the board does not compose without them. Not validated on their own. Mutated by the
  negative cases whose attribute lives on a pin or body inside the prototype (CG.002, CG.007,
  CG.012).

The suite covers: tier registration and entry-point discovery, with every requirement code of
the six features backed by a registered checker and each of the 38 codes in exactly one feature;
profile validation of the bundled conformant board and a planted-defect board under
`PCB-Assembly`, and of a bare board under `PCB-Board`; a negative matrix that applies one deliberate
violation at a time to a scratch copy of the conformant board and asserts that exactly the rule for
that code reports it at the stated severity (every registered code has at least one case, so a rule
added without one fails the suite); direct rule tests for the declared-gap
markers and the no-stuff conditional; and composition shapes that must not produce wrong verdicts —
unresolved component references (UO.012), invalid roles inside referenced package prototypes,
mixed local/external references, class masters outside the default prim, reference-strength
overrides, panels built from external board references, an unused board class beside its
placements, a pin association that contradicts the component in a second board scope, inherited
`strongerThanDescendants` material bindings (UO.017), a class mesh standing in for placed
instances, and revalidation of a stage edited after a previous run. Traversal visits every
distinct composed definition once, de-duplicated by composed identity with board scope for
identity-bearing prims.

The material check resolves direct, all-purpose `material:binding` relationships (strength and
inheritance honoured, prototype meshes evaluated under their placements). Collection-based and
purpose-specific bindings are not resolved — a stated alpha limitation; UO.017 skips, never
fails, meshes it cannot resolve.

For tier anatomy and build/publish instructions, see the foundation guide
(`nv_core/sr_specs/docs/guides/foundation_pypi.md`) and the tooling README
(`nv_core/tiers/_tooling/README.md`). The Python build command above also works
on Windows.
