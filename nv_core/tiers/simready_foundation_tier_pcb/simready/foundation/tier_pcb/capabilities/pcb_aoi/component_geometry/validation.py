# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
PCB Component Geometry (CG) validators — `pcb_usd_contract.md` §1–§3.

Placement, anchoring, pins, polarity, appearance and per-surface material fields on
each placed component prim (bearing `pcba:component:refdes`), plus the per-mesh material
class on every role-bearing Mesh. One rule per requirement code, so an exporter
gets a precise, per-code report.

Severity model:
  - a `MUST` field absent or out of vocabulary  → FAILURE
  - a relational / heuristic mismatch that instancing can legitimately hide → WARNING
  - a `pcba:prov:<attr> = "not_yet_available"` marker downgrades a missing field → WARNING

SRF-shaped: the only line that changes on a port is the `requirements` import.
"""
import usd_validation_nvidia
from pxr import Usd

from .. import _contract as C
import simready.foundation.tier_pcb.requirements as cap


def _require_component(checker, prim, leaf, req, vocab=None, allow_empty=False):
    """Shared MUST check for a `pcba:component:<leaf>` field, honoring the prov waiver."""
    attr = f"pcba:component:{leaf}"
    if not C.defined(prim, attr):
        if C.waived(prim, leaf):
            C.add_waived(checker, req, attr, prim)
        else:
            checker._AddFailedCheck(f"{req.code}: missing {attr} on {C.label(prim)}.",
                                    at=prim, requirement=req)
        return
    val = C.get(prim, attr)
    if not allow_empty and val in (None, ""):
        checker._AddFailedCheck(f"{req.code}: {attr} is declared but empty on {C.label(prim)}.",
                                at=prim, requirement=req)
        return
    if vocab is not None and val not in (None, "") and val not in vocab:
        checker._AddFailedCheck(f"{req.code}: {attr} '{val}' on {C.label(prim)} not in vocabulary.",
                                at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_001)
class PlacementChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.001 — Placement. `pcba:component:side` (in vocab), `nominalPosMm` and `nominalRotationDeg` declared.

    Contract: pcb_usd_contract.md §1–§2. These fix where the part sits on the board.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_001
        for prim in C.iter_components(stage):
            _require_component(self, prim, "side", req, vocab=C.SIDES)  # side is required for all, incl. fiducials
            if C.is_electrical(prim):  # placement pose is an electrical-part MUST; fiducials/mechanical exempt
                _require_component(self, prim, "nominalPosMm", req)
                _require_component(self, prim, "nominalRotationDeg", req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_002)
class AnchorChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.002 — Anchor & geometry reference.

    `pcba:component:anchor` (in vocab) + `pcba:component:bodyCentroidLocal` on the component, and
    `pcba:mesh:originOffset` on the body mesh. The requirements source groups mesh_origin_offset with
    placement_anchor + body_centroid_local as the "geometry reference" — the offset from the source
    *body* mesh origin to the anchor, not a per-pin field. Honors the `pcba:prov:originOffset` waiver.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_002
        for prim in C.iter_components(stage, electrical_only=True):
            _require_component(self, prim, "anchor", req, vocab=C.ANCHORS)
            _require_component(self, prim, "bodyCentroidLocal", req)
            for mesh in C.component_meshes(prim):
                if C.role_of(mesh) != "pkg_body":
                    continue  # geometry-reference offset is a body-level field, not per-pin
                if not C.defined(mesh, "pcba:mesh:originOffset"):
                    if C.waived(mesh, "originOffset"):
                        self._AddWarning(
                            f"CG.002: pcba:mesh:originOffset not yet available on body {mesh.GetPath()} "
                            f"of {C.label(prim)} (waived).",
                            at=mesh, requirement=req)
                    else:
                        self._AddFailedCheck(
                            f"CG.002: missing pcba:mesh:originOffset on body mesh {mesh.GetPath()} "
                            f"of {C.label(prim)}.",
                            at=mesh, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_003)
class BodyHeightChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.003 — Body height. `pcba:component:heightMm` declared; if a value is authored it must be > 0."""

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_003
        for prim in C.iter_components(stage, electrical_only=True):
            _require_component(self, prim, "heightMm", req)
            val = C.get(prim, "pcba:component:heightMm")
            if val is not None and val <= 0:
                self._AddFailedCheck(f"CG.003: pcba:component:heightMm {val} on {C.label(prim)} must be > 0.",
                                     at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_005)
class PinCountChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.005 — Pin count. `pcba:component:pinCount` declared and > 0.

    Relational: if the component's pin prims are present and their count differs from
    `pinCount`, warn (not fail — instancing can hide pins from a shared prototype).
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_005
        for prim in C.iter_components(stage, electrical_only=True):
            attr = "pcba:component:pinCount"
            if not C.defined(prim, attr):
                if C.waived(prim, "pinCount"):
                    C.add_waived(self, req, attr, prim)
                else:
                    self._AddFailedCheck(f"CG.005: missing {attr} on {C.label(prim)}.",
                                         at=prim, requirement=req)
                continue
            count = C.get(prim, attr)
            if count is None or count <= 0:
                self._AddFailedCheck(f"CG.005: {attr} on {C.label(prim)} must be > 0 (got {count}).",
                                     at=prim, requirement=req)
                continue
            pins = C.pins_of(prim)
            if pins and len(pins) != count:
                self._AddWarning(
                    f"CG.005: {attr} = {count} but {len(pins)} pin prim(s) found on {C.label(prim)}.",
                    at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_006)
class PinPitchChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.006 — Pin pitch. When `pinCount` > 2, `pcba:component:pinPitchMm` MUST be declared.

    A pitch is only meaningful for multi-pin parts; 2-pin (or undeclared) parts are skipped.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_006
        for prim in C.iter_components(stage):
            count = C.get(prim, "pcba:component:pinCount")
            if count is None or count <= 2:
                continue
            _require_component(self, prim, "pinPitchMm", req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_007)
class PinGeometryChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.007 — Pin geometry. Each pin declares `pcba:pin:solderable`; any `pcba:pin:crossSection` and
    `pcba:pin:terminalType` (optional) are in vocabulary when authored.

    Also: `pcba:pin:number` MUST be **unique within a component**. §10 calls it a "stable
    id" and BG.012 resolves a board site's `componentPinNumber` against it — neither works if a number
    names two pins, and the pipeline would place one joint's solder on whichever it hit first.

    Note that `pinCount` (CG.005) does NOT catch this: it counts pin *prims*, so a part with seven
    pin prims matches its declared 7 while carrying only five distinct numbers.

    A duplicate is treated as a genuine collision rather than one pin split across two meshes, because
    the contract's unit of a pin IS the prim bearing the number (that is what `pins_of` and CG.005
    count); two prims sharing a number are two leads.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_007
        for prim in C.iter_components(stage):
            self._check_pin_numbers_unique(prim, req)
            for pin in C.pins_of(prim):
                if not C.defined(pin, "pcba:pin:solderable"):
                    if C.waived(pin, "solderable"):
                        C.add_waived(self, req, "pcba:pin:solderable", pin,
                                     context=f"of {C.label(prim)}")
                    else:
                        self._AddFailedCheck(
                            f"CG.007: missing pcba:pin:solderable on pin {pin.GetPath()} of {C.label(prim)}.",
                            at=pin, requirement=req)
                else:
                    # `solderable` is a bool: "does this contact form a solder joint?" A MUST-level pin
                    # attribute needs both a type and a value domain, or an exporter cannot author it.
                    val = C.get(pin, "pcba:pin:solderable")
                    if not isinstance(val, bool):
                        self._AddFailedCheck(
                            f"CG.007: pcba:pin:solderable on pin {pin.GetPath()} of {C.label(prim)} is "
                            f"{type(val).__name__} '{val}' - it must be a bool (does this contact form a "
                            f"solder joint?).",
                            at=pin, requirement=req)
                if C.defined(pin, "pcba:pin:crossSection"):
                    xs = C.get(pin, "pcba:pin:crossSection")
                    if xs not in (None, "") and xs not in C.CROSS_SECTIONS:
                        self._AddFailedCheck(
                            f"CG.007: pcba:pin:crossSection '{xs}' on pin {pin.GetPath()} "
                            f"of {C.label(prim)} not in vocabulary.",
                            at=pin, requirement=req)
                if C.defined(pin, "pcba:pin:terminalType"):
                    tt = C.get(pin, "pcba:pin:terminalType")
                    if tt not in (None, "") and tt not in C.TERMINAL_TYPES:
                        self._AddFailedCheck(
                            f"CG.007: pcba:pin:terminalType '{tt}' on pin {pin.GetPath()} "
                            f"of {C.label(prim)} not in vocabulary.",
                            at=pin, requirement=req)
                    elif tt == "mixed":
                        # `mixed` says the part's pin forms vary without saying what they are — the
                        # actual forms go in `pcba:component:terminalTypes`, mirroring
                        # `processClass = Mixed` -> `processClasses`.
                        forms = C.get(prim, "pcba:component:terminalTypes")
                        if not forms:
                            self._AddFailedCheck(
                                f"CG.007: pin {pin.GetPath()} of {C.label(prim)} has terminalType "
                                f"'mixed' but the component authors no pcba:component:terminalTypes — "
                                f"'mixed' must name the actual forms it combines.",
                                at=pin, requirement=req)
                        else:
                            bad = [f for f in forms if f not in C.TERMINAL_TYPE_MEMBERS]
                            if bad:
                                self._AddFailedCheck(
                                    f"CG.007: pcba:component:terminalTypes on {C.label(prim)} contains "
                                    f"{bad} — members must be terminal forms (not 'mixed' itself).",
                                    at=prim, requirement=req)
                # `pcba:pin:designator` (OPTIONAL): the source netlist/CAD pin designator,
                # preserved when `pcba:pin:number` is positional. Any non-empty string is valid; only
                # an authored-but-empty value is worth flagging.
                if C.defined(pin, "pcba:pin:designator"):
                    d = C.get(pin, "pcba:pin:designator")
                    if d is not None and str(d).strip() == "":
                        self._AddWarning(
                            f"CG.007: pcba:pin:designator on pin {pin.GetPath()} of {C.label(prim)} "
                            f"is authored but empty.",
                            at=pin, requirement=req)

    def _check_pin_numbers_unique(self, comp, req) -> None:
        """`pcba:pin:number` must name exactly one pin within a component (see class docstring)."""
        by_number = {}
        for pin in C.pins_of(comp):
            n = C.get(pin, "pcba:pin:number")
            if n is None:
                continue  # absence is CG.007's per-pin concern, not a collision
            by_number.setdefault(str(n), []).append(pin)
        for number, pins in sorted(by_number.items()):
            if len(pins) < 2:
                continue
            names = ", ".join(p.GetPath().name for p in pins)
            self._AddFailedCheck(
                f"CG.007: pcba:pin:number '{number}' is carried by {len(pins)} pins of "
                f"{C.label(comp)} ({names}) — a pin number must identify exactly one pin, or a board "
                f"site naming it cannot resolve to a single joint (§10, BG.012).",
                at=pins[1], requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_008)
class Pin1PositionChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.008 — Pin-1 position (heuristic). Warn if the part looks keyed but lacks `pcba:component:pin1PosMm`.

    "Keyed" is not reliably detectable, so this is advisory only: if the part declares a
    `polarityType` or has more than 2 pins, a missing `pin1PosMm` warrants a warning — never a fail.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_008
        for prim in C.iter_components(stage):
            count = C.get(prim, "pcba:component:pinCount")
            keyed = C.defined(prim, "pcba:component:polarityType") or (count is not None and count > 2)
            if keyed and not C.defined(prim, "pcba:component:pin1PosMm"):
                self._AddWarning(
                    f"CG.008: {C.label(prim)} looks keyed (polarityType or >2 pins) "
                    f"but has no pcba:component:pin1PosMm.",
                    at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_009)
class PolarityChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.009 — Polarity type. If `pcba:component:polarityType` is declared, its value must be in vocab.

    No presence requirement — whether a part is polarized is not detectable from geometry.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_009
        for prim in C.iter_components(stage):
            if not C.defined(prim, "pcba:component:polarityType"):
                continue
            val = C.get(prim, "pcba:component:polarityType")
            if val not in (None, "") and val not in C.POLARITY_TYPES:
                self._AddFailedCheck(
                    f"CG.009: pcba:component:polarityType '{val}' on {C.label(prim)} not in vocabulary.",
                    at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_010)
class MarkingsChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.010 — Markings (advisory). If `pcba:component:markings` is declared but empty, warn."""

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_010
        for prim in C.iter_components(stage):
            if C.defined(prim, "pcba:component:markings") and C.get(prim, "pcba:component:markings") in (None, ""):
                self._AddWarning(
                    f"CG.010: pcba:component:markings is declared but empty on {C.label(prim)}.",
                    at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_011)
class AppearanceChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.011 — Nominal appearance. `bodyColorNominal` declared; `finishNominal` and `materialClassNominal` in vocab."""

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_011
        for prim in C.iter_components(stage, electrical_only=True):
            _require_component(self, prim, "bodyColorNominal", req)
            _require_component(self, prim, "finishNominal", req, vocab=C.FINISHES)
            _require_component(self, prim, "materialClassNominal", req, vocab=C.MATERIAL_CLASSES)


@usd_validation_nvidia.register_rule("PCB-ComponentGeometry")
@usd_validation_nvidia.register_requirements(cap.ComponentGeometryRequirements.CG_012)
class SurfaceMaterialChecker(usd_validation_nvidia.BaseRuleChecker):
    """CG.012 — Per-surface material class.

    For **board** roles the material class is implied by the role
    (`board_copper`→copper, `board_silk`→silkscreen, …), so `matClass` is **derived from role** and need
    not be authored. Explicit `pcba:mesh:matClass` is required where the role does NOT imply a material
    (`C.MATCLASS_REQUIRED_ROLES`): **`pkg_*`**, because a body may be plastic or ceramic, and
    **`fixture_*`**, because a carrier may be machined aluminium or a composite. Any
    authored value is validated against the vocabulary. Role↔material agreement is enforced by UO.017.

    Contract: pcb_usd_contract.md §9.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentGeometryRequirements.CG_012
        attr = "pcba:mesh:matClass"
        for mesh in C.iter_meshes(stage):
            role = C.role_of(mesh)
            if role is None:
                continue
            if not C.defined(mesh, attr):
                if role not in C.MATCLASS_REQUIRED_ROLES:
                    continue  # derived from role — explicit matClass not required
                if C.waived(mesh, "matClass"):
                    C.add_waived(self, req, attr, mesh)
                else:
                    self._AddFailedCheck(
                        f"CG.012: missing {attr} on {mesh.GetPath()} - required on {role}, whose "
                        f"material is not implied by its role.",
                        at=mesh, requirement=req)
                continue
            val = C.get(mesh, attr)
            if val in (None, ""):
                self._AddFailedCheck(f"CG.012: {attr} is declared but empty on {mesh.GetPath()}.",
                                     at=mesh, requirement=req)
            elif val not in C.MESH_MAT_CLASSES:
                self._AddFailedCheck(f"CG.012: {attr} '{val}' on {mesh.GetPath()} not in vocabulary.",
                                     at=mesh, requirement=req)
