# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
PCB Board Geometry (BG) validators — `pcb_usd_contract.md` §3–§4, §8.

Board-level geometry: board thickness, copper and mask layers, pads, solder paste,
THT barrels, and site occupancy and association. One rule per requirement code, so
an exporter gets a precise, per-code report.

Severity model:
  - a `MUST` field absent or out of vocabulary  → FAILURE
  - advisory conditions                          → WARNING
  - a `pcba:prov:<attr> = "not_yet_available"` marker downgrades a missing field → WARNING

SRF-shaped: the only line that changes on a port is the `requirements` import.
"""
import math

import usd_validation_nvidia
from pxr import Gf, Usd, UsdGeom

from .. import _contract as C
import simready.foundation.tier_pcb.requirements as cap


def _meshes_with_role(stage: Usd.Stage, role: str):
    """Every Mesh prim whose `pcba:mesh:role` equals `role`."""
    return [m for m in C.iter_meshes(stage) if C.role_of(m) == role]


def _rel_targets(prim: Usd.Prim, name: str):
    """Authored targets of relationship `name`, or [] if absent/invalid.

    Reads both namespace spellings: falls back to `pcb:`.
    """
    return C.relationship_targets(prim, name)


def _require_declared(checker, prim, attr, req, vocab=None):
    """MUST check: `attr` declared on `prim`, optionally with its value in `vocab`.

    Delegates to `C.require_declared`, which honors the §14 `pcba:prov:` waiver.
    """
    return C.require_declared(checker, prim, attr, req, vocab=vocab)


@usd_validation_nvidia.register_rule("PCB-BoardGeometry")
@usd_validation_nvidia.register_requirements(cap.BoardGeometryRequirements.BG_001)
class BoardThicknessChecker(usd_validation_nvidia.BaseRuleChecker):
    """BG.001 — Board thickness. The board-root prim declares `pcba:board:thicknessMm`,
    and any authored value MUST be > 0.

    Contract: pcb_usd_contract.md §3. Physical board stack-up thickness in millimeters. The board root
    is discovered by attribute (it may sit under a scene wrapper), not assumed to be the default prim.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.BoardGeometryRequirements.BG_001
        attr = "pcba:board:thicknessMm"
        dp = C.board_root(stage)
        if not dp:
            return  # no board-root prim; absence reported by UO.001
        if not C.defined(dp, attr):
            self._AddFailedCheck(f"{req.code}: missing {attr} on board root {C.label(dp)}.",
                                 at=dp, requirement=req)
            return
        val = C.get(dp, attr)
        if val is not None and val <= 0:
            self._AddFailedCheck(f"{req.code}: {attr} '{val}' on {C.label(dp)} must be > 0.",
                                 at=dp, requirement=req)


@usd_validation_nvidia.register_rule("PCB-BoardGeometry")
@usd_validation_nvidia.register_requirements(cap.BoardGeometryRequirements.BG_002)
class BoardLayersChecker(usd_validation_nvidia.BaseRuleChecker):
    """BG.002 — Copper & solder-mask geometry present.

    The requirements source makes copper-layer geometry and solder-mask geometry a MUST (conductive
    surfaces + production-accurate board color/finish). A conformant board carries at least one
    `board_copper` and one `board_mask` mesh.
    Contract: pcb_usd_contract.md §5 (Board & layers).
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.BoardGeometryRequirements.BG_002
        roles = {C.role_of(m) for m in C.iter_meshes(stage)}
        if "board_copper" not in roles:
            self._AddFailedCheck("BG.002: no Mesh with role 'board_copper' (copper-layer geometry missing).",
                                 at=stage, requirement=req)
        if "board_mask" not in roles:
            self._AddFailedCheck("BG.002: no Mesh with role 'board_mask' (solder-mask geometry missing).",
                                 at=stage, requirement=req)


@usd_validation_nvidia.register_rule("PCB-BoardGeometry")
@usd_validation_nvidia.register_requirements(cap.BoardGeometryRequirements.BG_003)
class PlatedBarrelChecker(usd_validation_nvidia.BaseRuleChecker):
    """BG.003 - `board_barrel` geometry at occupied through-hole joints.

    Two scoping principles:

    1. The barrel requirement is scoped to joints that are actually inspected, not to every plated hole.
       A plated via with nothing in it forms no solder joint (a real panel has an order of magnitude more
       plated holes than occupied ones; barrels for the unoccupied ones buy nothing).
    2. There is no `pcba:board:plated` flag. A barrel *is* the plating, so a prim carrying one cannot be
       unplated and a flag would only restate its own presence. Unplated holes are outside the contract's
       interest: no barrel, no attributes, and where a screw sits in one the `mechanical` part
       describes it (§8.1).

    With `board_hole` optional, a stage may contain no hole prims at all, so this checks the other
    direction: if a through-hole component is placed, its joints need barrels.

    Check:
        - every joint of a placed THT component has a `board_barrel` carrying its `refdes` +
          `componentPinNumber` (MUST). Where the stage has **no** barrel geometry at all, that is
          reported once, naming the joint count, rather than once per joint - the fix is the same
          single omission and N identical lines would only bury it.

    Reported per joint, not once per stage: a board missing every barrel and a board missing one
    barrel must not produce the same single finding, and a total absence of barrels must not read as
    a rounding error next to thousands of pad findings. The barrel is one of the three prims a THT
    joint is made of (§6), so its scale matters.

    `press_fit` counts: it is effectively a solderless through-hole part, so the hole is plated, the
    barrel is real, and the camera looks down it. Whether *solder-defect classes* apply there is a
    separate question, answered per pin by `pcba:pin:solderable` (§12) - describing the hole and
    inspecting the joint are not the same question.

    What is a joint: a pin that is solderable, or a press-fit pin (terminal form `pressFit`, or the
    part's process class is `press_fit`). A non-solderable pin that is not press-fit - a locating peg,
    a mechanical lead in an unplated hole - forms no joint, and an unplated hole carries nothing (§6),
    so no barrel is owed for it.
    """

    @staticmethod
    def _is_joint(pin, comp) -> bool:
        if C.get(pin, "pcba:pin:solderable") is True:
            return True
        if C.get(pin, "pcba:pin:terminalType") == "pressFit":
            return True
        return C.process_class(comp) == "press_fit"

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.BoardGeometryRequirements.BG_003
        tht = [c for c in C.iter_components(stage) if C.is_tht(c)]
        if not tht:
            return
        barrels = _meshes_with_role(stage, "board_barrel")

        # The joints a THT component brings: one per pin.
        joints = []
        for comp in tht:
            ident = C.identity(comp)
            if ident is None:
                continue
            for pin in C.pins_of(comp):
                n = C.get(pin, "pcba:pin:number")
                if n is not None and self._is_joint(pin, comp):
                    joints.append((ident, str(n), comp))

        if not joints:
            return
        if not barrels:
            self._AddFailedCheck(
                f"BG.003: no board_barrel geometry anywhere on the board, but {len(tht)} through-hole "
                f"component(s) are placed with {len({(r, p) for r, p, _ in joints})} joint(s) between "
                f"them. The barrel is the plating through the hole and one of the three prims a THT "
                f"joint is made of (§6); without it there is no through-hole copper to inspect.",
                at=stage, requirement=req)
            return

        claimed = set()
        for b in barrels:
            rd = C.get(b, "pcba:board:refdes")
            attr = C.board_pin_number_attr(b)
            pin = C.get(b, attr) if attr else None
            if rd and pin is not None:
                claimed.add((rd, str(pin)))
        for ident, n, comp in joints:
            if (ident, n) not in claimed:
                self._AddFailedCheck(
                    f"BG.003: {ident} pin '{n}' has no board_barrel carrying its refdes + "
                    f"componentPinNumber — a through-hole joint needs the plating through the hole (§6).",
                    at=comp, requirement=req)


@usd_validation_nvidia.register_rule("PCB-BoardGeometry")
@usd_validation_nvidia.register_requirements(cap.BoardGeometryRequirements.BG_005)
class PadNumberChecker(usd_validation_nvidia.BaseRuleChecker):
    """BG.005 — Pad number. Every `board_pad` Mesh declares a non-empty `pcba:board:padNumber`."""

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.BoardGeometryRequirements.BG_005
        attr = "pcba:board:padNumber"
        for prim in _meshes_with_role(stage, "board_pad"):
            if not C.defined(prim, attr):
                if C.waived(prim, "padNumber"):
                    C.add_waived(self, req, attr, prim)
                else:
                    self._AddFailedCheck(f"{req.code}: missing {attr} on {C.label(prim)}.",
                                         at=prim, requirement=req)
            elif C.get(prim, attr) in (None, ""):
                self._AddFailedCheck(f"{req.code}: {attr} is declared but empty on {C.label(prim)}.",
                                     at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-BoardGeometry")
@usd_validation_nvidia.register_requirements(cap.BoardGeometryRequirements.BG_007)
class PasteAssociationChecker(usd_validation_nvidia.BaseRuleChecker):
    """BG.007 — Paste association (when paste supplied).

    The association is the **same `pcba:board:refdes` + `componentPinNumber` pair a pad or barrel
    uses** (BG.012) - a paste deposit naming its contact is the same statement, so it does not get its
    own attribute names. `pcba:board:pasteFor` is SHOULD.

    Same two reasons as BG.012: a refdes survives stage restructuring and re-panelization where a prim
    path does not, and the pair is authorable *before* the component prim exists. That second one is
    what matters here - on a staged export a paste deposit has no `pasteFor` target to point at, not
    because the exporter does not know the contact but because there is no prim to point at yet.
    """

    _REFDES = "pcba:board:refdes"
    _PIN = C.BOARD_PIN_NUMBER

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.BoardGeometryRequirements.BG_007
        for prim in _meshes_with_role(stage, "board_paste"):
            # A no-stuff site is pasted but has no contact to resolve to, so the association is
            # conditional on the associated pad being occupied. We cannot see that from the paste prim,
            # so an explicit `occupied = false` on the deposit exempts it.
            if C.get(prim, "pcba:board:occupied") is False:
                continue
            if C.defined(prim, self._REFDES):
                if not C.defined(prim, self._PIN):
                    self._AddFailedCheck(
                        f"{req.code}: {C.label(prim)} has {self._REFDES} but no {self._PIN} - the "
                        f"association is the pair.", at=prim, requirement=req)
                continue
            # Alternative form: the rel alone still satisfies the requirement, with a nudge.
            if _rel_targets(prim, "pcba:board:pasteFor"):
                self._AddWarning(
                    f"{req.code}: {C.label(prim)} associates paste by rel only - prefer "
                    f"{self._REFDES} + {self._PIN}, which survives restructuring and can be authored "
                    f"before the component prim exists.", at=prim, requirement=req)
                continue
            if C.waived(prim, "refdes") or C.waived(prim, "pasteFor"):
                C.add_waived(self, req, self._REFDES, prim)
            else:
                self._AddFailedCheck(
                    f"{req.code}: {C.label(prim)} board_paste has no {self._REFDES} + {self._PIN} "
                    f"(which contact this deposit is for).", at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-BoardGeometry")
@usd_validation_nvidia.register_requirements(cap.BoardGeometryRequirements.BG_008)
class PasteSideChecker(usd_validation_nvidia.BaseRuleChecker):
    """BG.008 — Paste side (when paste supplied). Every `board_paste` Mesh's side must be determinable:
    either `pcba:board:solderLayer` authored on the mesh (top/bottom), or derivable from the containing
    layer prim's `pcba:layer:side`.

    The side may be derived from the layer hierarchy rather than authored
    on every paste pad — paste pads are grouped under side-named layer prims (`SideTop_SolderPasteLayer_*`),
    so the side is already unambiguous. The paste↔component association (`pcba:board:pasteFor`, BG.007) is
    NOT relaxed — it stays authored per pad.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.BoardGeometryRequirements.BG_008
        for prim in _meshes_with_role(stage, "board_paste"):
            if C.defined(prim, "pcba:board:solderLayer"):
                val = C.get(prim, "pcba:board:solderLayer")
                if val not in C.SOLDER_LAYERS:
                    self._AddFailedCheck(
                        f"{req.code}: pcba:board:solderLayer '{val}' on {C.label(prim)} not in vocabulary.",
                        at=prim, requirement=req)
            elif C.layer_side(prim) is None:
                self._AddFailedCheck(
                    f"{req.code}: {C.label(prim)} board_paste has no pcba:board:solderLayer and no "
                    f"derivable layer side (pcba:layer:side on an ancestor).",
                    at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-BoardGeometry")
@usd_validation_nvidia.register_requirements(cap.BoardGeometryRequirements.BG_010)
class HoleGeometryChecker(usd_validation_nvidia.BaseRuleChecker):
    """BG.010 — Hole & pad geometry (THT). Hole geometry is declared on the **`board_barrel`**.

    Three points:

    1. **The barrel carries the hole data, not `board_hole`.** With `board_hole` prims optional
       (§6), the barrel is the prim guaranteed to exist wherever a THT joint exists, so it is the
       reliable home for centre/shape/dims. There is no `holeSide` - a through-hole goes all
       the way through the board, so a side is not meaningful for it.
    2. **A drill radius satisfies the requirement.** This is an *input* contract: it asks for what an
       exporter actually has. An exporter holding only `holeRadiusMm` may author that and let the
       consumer derive centre, shape and dims from it plus the prim transform. Demanding the derived
       spelling would fail data that is entirely present.
    3. **A contoured non-circular hole derives its centre.** An exporter may describe slots by
       shape + dims + the full contour mesh, without `holeCenterMm` — the centre is trivially derivable
       from the geometry's extent, the same "ask for what the exporter has" principle as the radius
       form. So `holeCenterMm` is required only when neither a radius form nor (shape + dims +
       geometry extent) is present.

    Pad definition: a `board_pad`'s extent is the **exposed pad = the solder-mask
    opening**, not a per-pad copper contour (the copper underneath may be one continuous pour). Pads must
    still be individually addressable prims carrying `padNumber` (BG.005). This rule enforces only the
    hole fields; the pad *shape* is not machine-checked.
    """

    _FIELDS = (
        "pcba:board:holeCenterMm",
        "pcba:board:holeShape",
        "pcba:board:holeDimsMm",
    )
    # Any one of these means the exporter has stated the hole size in a form we can derive from.
    _RADIUS_FORMS = ("pcba:board:holeRadiusMm", "pcba:board:holeDiameterMm")

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.BoardGeometryRequirements.BG_010
        for prim in _meshes_with_role(stage, "board_barrel"):
            if any(C.defined(prim, a) for a in self._RADIUS_FORMS):
                continue  # derivable: radius + prim transform gives centre, shape and dims
            for attr in self._FIELDS:
                if attr == "pcba:board:holeCenterMm" and not C.defined(prim, attr):
                    # Contoured form: shape + dims + geometry -> centre derives from the extent.
                    if (C.defined(prim, "pcba:board:holeShape")
                            and C.defined(prim, "pcba:board:holeDimsMm")
                            and prim.GetAttribute("extent").Get()):
                        continue
                _require_declared(self, prim, attr, req)


@usd_validation_nvidia.register_rule("PCB-BoardGeometry")
@usd_validation_nvidia.register_requirements(cap.BoardGeometryRequirements.BG_012)
class HoleOccupancyChecker(usd_validation_nvidia.BaseRuleChecker):
    """BG.012 — Site occupancy + association, for BOTH holes and pads.

    Three points:

    1. **Occupancy is not a through-hole concept.** An SMT pad is exactly as capable of being
       unoccupied as an empty through-hole, so `pcba:board:occupied` is required on `board_pad`
       as well as `board_barrel`.
    2. **Intentionally unpopulated ("no-stuff") sites.** A pad can be fully fabricated, pasted and
       reflowed and receive no component *by design* — the artwork is left alone and the placement
       machine is simply told to skip it. An AOI system must not report that as a missing component.
       So when `occupied = false`, the site MUST also declare `pcba:board:intentionallyUnpopulated`
       (bool) to separate "empty on purpose" from "part is missing". Without it the two are
       indistinguishable in the geometry, and every no-stuff site becomes a false positive.

    3. **The association is the `refdes` + `componentPinNumber` pair.** When occupied, the
       site MUST carry `pcba:board:refdes` and `pcba:board:componentPinNumber` (a bare
       `pcba:pin:number` on the board prim is also accepted, with a warning). A refdes survives stage
       restructuring, re-panelization and re-instancing where a prim path does not, and it is authorable
       before the component prim exists - which matters, because an exporter staging board copper ahead
       of component geometry cannot emit a single `rel`.

       `pcba:board:component` is **SHOULD**, not MUST: author it when the component prim is in the
       file, and its absence is not a failure. Where both are present they MUST agree, and the pair wins.
    """

    # The THT site is the `board_barrel`, not `board_hole` - the barrel carries the hole data because
    # `board_hole` prims are optional (§6, §10).
    _SITE_ROLES = ("board_barrel", "board_pad")

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.BoardGeometryRequirements.BG_012
        for role in self._SITE_ROLES:
            for prim in _meshes_with_role(stage, role):
                self._check_site(prim, role, req)
        self._check_association_resolves(stage, req)
        self._check_one_site_per_side(stage, req)
        self._check_association_matches_geometry(stage, req)

    def _check_site(self, prim, role, req) -> None:
        if not C.defined(prim, "pcba:board:occupied"):
            # Unknown occupancy is a declared gap, not `occupied = false`:
            # `occupied` is a positive claim about the site, so an exporter that has not resolved
            # occupancy omits it and marks `pcba:prov:occupied`. While marked, the site owes
            # neither the association pair nor `intentionallyUnpopulated` (the early return).
            if C.waived(prim, "occupied"):
                C.add_waived(self, req, "pcba:board:occupied", prim)
            else:
                self._AddFailedCheck(
                    f"{req.code}: missing pcba:board:occupied on {role} {C.label(prim)}.",
                    at=prim, requirement=req)
            return

        if C.get(prim, "pcba:board:occupied") is True:
            # The association is the refdes + componentPinNumber pair.
            if not C.defined(prim, "pcba:board:refdes"):
                if C.waived(prim, "refdes"):
                    C.add_waived(self, req, "pcba:board:refdes", prim)
                else:
                    self._AddFailedCheck(
                        f"{req.code}: occupied {role} {C.label(prim)} has no pcba:board:refdes "
                        f"(which component's terminal lands here).",
                        at=prim, requirement=req)
            # `pcba:board:component` is SHOULD - a direct handle when the component prim exists. Its
            # absence is not reported at all: on a staged export the prim legitimately doesn't exist yet.
            # But if it IS authored it must agree with the refdes, and the pair wins.
            targets = _rel_targets(prim, "pcba:board:component")
            rd = C.get(prim, "pcba:board:refdes")
            if targets and rd:
                stage = prim.GetStage()
                names = {C.identity(t) for t in (stage.GetPrimAtPath(p) for p in targets) if t and t.IsValid()}
                names.discard(None)
                if names and rd not in names:
                    self._AddFailedCheck(
                        f"{req.code}: {C.label(prim)} pcba:board:component resolves to {sorted(names)} "
                        f"but pcba:board:refdes is '{rd}' - they must agree.",
                        at=prim, requirement=req)
            attr = C.board_pin_number_attr(prim)
            if attr is None:
                self._AddFailedCheck(
                    f"{req.code}: occupied {role} {C.label(prim)} missing {C.BOARD_PIN_NUMBER} "
                    f"(which pin of that component lands here).",
                    at=prim, requirement=req)
            elif attr == C.BOARD_PIN_NUMBER_LEGACY:
                self._AddWarning(
                    f"{req.code}: {C.label(prim)} uses legacy '{C.BOARD_PIN_NUMBER_LEGACY}' on a board "
                    f"prim — rename to '{C.BOARD_PIN_NUMBER}'. Boards have pads; components have pins.",
                    at=prim, requirement=req)
            return

        # Unoccupied → the no-stuff distinction is mandatory, but on PADS only. An empty
        # barrel is a via: nothing was ever meant to go in it and nothing inspects it, so "empty on
        # purpose vs part missing" is not a question that arises.
        if role != "board_pad":
            return
        if not C.defined(prim, "pcba:board:intentionallyUnpopulated"):
            if C.waived(prim, "intentionallyUnpopulated"):
                # An exporter that genuinely cannot tell no-stuff from missing may declare the gap (§14)
                # rather than guess `false`. This is a tracked blocker, not a pass: the board still can't
                # be inspected without it. It shows in the report's `waived` count.
                C.add_waived(self, req, "pcba:board:intentionallyUnpopulated", prim,
                             context=f"on unoccupied {role}")
            else:
                self._AddFailedCheck(
                    f"{req.code}: unoccupied {role} {C.label(prim)} does not declare "
                    f"pcba:board:intentionallyUnpopulated — a no-stuff site and a missing component are "
                    f"indistinguishable without it.",
                    at=prim, requirement=req)


# --------------------------------------------------------------------------------------------- #
# BG.012, second pass: does the association RESOLVE?
# --------------------------------------------------------------------------------------------- #
    # Roles that carry the association. Wider than `_SITE_ROLES` above: paste also names its contact
    # (BG.007) with the same pair, so a mis-numbered paste deposit is the same defect.
    _ASSOC_ROLES = ("board_pad", "board_barrel", "board_paste")

    def _check_association_resolves(self, stage: Usd.Stage, req) -> None:
        """The `refdes` + `componentPinNumber` pair must RESOLVE, not merely exist.

        `_check_site` verifies the pair is *declared*; this verifies it is *correct*. §10 requires
        `componentPinNumber` to "match that component's `pcba:pin:number`", so this implements a
        requirement the contract states rather than adding one — a site naming pin 2 of a part that
        has no pin 2 must not pass silently. A missing or wrong pin/pad association puts simulated
        solder on the wrong joint, so the component pin <-> solder pad association is verified explicitly.

        Checks:
            - a site's `componentPinNumber` exists on the component its `refdes` names (FAILURE)
            - a solderable pin no board site claims (WARNING — the "missing" half)
            - how many associations could not be verified at all (ONE summary warning)

        Scoping — deliberate, and the reason this is usable at all: an *unresolvable* refdes is NOT
        reported per site. A staged export authors board copper ahead of component geometry, which is
        exactly why `pcba:board:component` is SHOULD (§10); on such a stage most
        sites name a component prim that does not exist yet. Reporting those per site would bury
        the real findings under thousands of known-staging ones, so they are summarized once.
        Components with no pin prims authored are skipped for the same reason — absence of pins is not
        evidence of a wrong pin number.
        """
        # Component-side truth: identity -> the pin numbers that component actually has.
        # Every identity below is scoped to its board root (§8, §10: a refdes is unique and an
        # association resolves *within one board*, never across a panel). Two authored boards in one
        # stage — a panel's positions plus a library master, say — therefore never share pins or
        # sites.
        comp_pins = {}
        for comp in C.iter_components(stage):
            ident = C.identity(comp)
            if ident is None:
                continue
            comp_pins[(C.board_root_of(comp), ident)] = {
                str(n) for n in (C.get(p, "pcba:pin:number") for p in C.pins_of(comp)) if n is not None
            }

        claimed = {}          # identity -> pin numbers claimed by board geometry
        pad_sides = {}        # (identity, pin) -> sides ('top'/'bottom') of the board_pads claiming it
        unverifiable = 0
        unknown = set()

        for prim in C.iter_meshes(stage):
            role = C.role_of(prim)
            if role not in self._ASSOC_ROLES:
                continue
            rd = C.get(prim, "pcba:board:refdes")
            if not rd:
                continue  # absence of the association is _check_site / BG.007's job, not this pass's
            attr = C.board_pin_number_attr(prim)
            pin = C.get(prim, attr) if attr else None
            if pin is None:
                continue
            pin = str(pin)
            sid = (C.board_root_of(prim), rd)
            claimed.setdefault(sid, set()).add(pin)
            if role == "board_pad":
                side = C.layer_side(prim)
                if side:
                    pad_sides.setdefault((sid, pin), set()).add(side)

            pins = comp_pins.get(sid)
            if pins is None:
                unverifiable += 1
                unknown.add(rd)
            elif pins and pin not in pins:
                self._AddFailedCheck(
                    f"{req.code}: {C.label(prim)} associates to {rd} pin '{pin}', but {rd} has no such "
                    f"pin (its pins: {sorted(pins)}) — the association cannot resolve.",
                    at=prim, requirement=req)

        # The "missing" half, two levels:
        #
        # 1. No site of any kind claims the pin -> WARNING (the contract requires a site to name its
        #    pin, not (yet) that every pin be named by a site).
        # 2. THT only: no SOLDER-SIDE ring carries the association -> FAILURE. §6 makes all three of a
        #    THT joint's prims carry the pair, and the solder-side ring is the one the joint actually
        #    forms on — it is what §13 derives the joint_roi from. Checked on its own rather than left
        #    to BG.003's barrel finding: a barrel and its solder-side ring are commonly unassociated
        #    together, and fixing only the barrels would leave real missing associations invisible.
        #    The solder side is the face opposite the component's mount side. Skipped when the
        #    component states no side, or when no pad side is derivable (no layer metadata) — absence
        #    of evidence is not a finding.
        for comp in C.iter_components(stage):
            ident = C.identity(comp)
            sid = (C.board_root_of(comp), ident)
            if not comp_pins.get(sid):
                continue
            got = claimed.get(sid, set())
            is_tht = C.is_tht(comp)
            mount = C.get(comp, "pcba:component:side")
            solder_side = {"top": "bottom", "bottom": "top"}.get(mount)
            for p in C.pins_of(comp):
                n = C.get(p, "pcba:pin:number")
                if n is None:
                    continue
                n = str(n)
                if C.get(p, "pcba:pin:solderable") is False:
                    continue  # forms no joint (§12), so it needs no board-side site
                if n not in got:
                    self._AddWarning(
                        f"{req.code}: {ident} pin '{n}' is claimed by no board_pad/board_barrel/"
                        f"board_paste — that joint has no board-side site.",
                        at=p, requirement=req)
                    continue
                if is_tht and solder_side:
                    sides = pad_sides.get((sid, n))
                    if sides is not None and solder_side not in sides:
                        self._AddFailedCheck(
                            f"{req.code}: {ident} pin '{n}' has no {solder_side}-side (solder-side) "
                            f"board_pad carrying its refdes + componentPinNumber — the joint forms on "
                            f"that ring, and §6 requires the association on all three of a THT joint's "
                            f"prims. Sides found: {sorted(sides)}.",
                            at=p, requirement=req)

        if unverifiable:
            self._AddWarning(
                f"{req.code}: {unverifiable} board site(s) name {len(unknown)} refdes with no component "
                f"prim on this stage, so the association could not be verified. Expected while component "
                f"geometry is staged behind board copper; re-check once the parts land.",
                at=stage, requirement=req)

    def _check_one_site_per_side(self, stage: Usd.Stage, req) -> None:
        """At most one `board_pad` per joint **per side**, and one `board_barrel` per joint (§6).

        Keyed on side: a through-hole terminal legitimately has copper on both faces, so one joint is
        three prims - component-side ring, solder-side ring, barrel - all carrying the same `refdes` +
        `componentPinNumber`. Two pads on the *same* side is the real defect: an extra `pad_ring_roi`
        for a joint that does not exist. Without the side in the key, every legitimate top/bottom ring
        pair would read as a duplicate.

        `board_paste` is deliberately excluded - a contact may take more than one deposit, and nothing
        downstream counts them.

        **Side is derived from the containing layer** (`C.layer_side`), because the contract defines no
        per-pad side attribute. §11.1 sanctions that derivation for paste `solderLayer`; this
        rule applies the same derivation to pads, and §13's "author `pad_ring_roi` per side" needs it too. A
        pad whose side cannot be determined is **skipped**, so an exporter that omits the layer metadata
        loses the check rather than collecting false duplicates.
        """
        by_slot = {}
        for prim in C.iter_meshes(stage):
            role = C.role_of(prim)
            if role not in ("board_pad", "board_barrel"):
                continue
            rd = C.get(prim, "pcba:board:refdes")
            attr = C.board_pin_number_attr(prim)
            pin = C.get(prim, attr) if attr else None
            if not rd or pin is None:
                continue
            # A barrel is one per joint; a pad is one per joint per side.
            if role == "board_pad":
                side = C.layer_side(prim)
                if side is None:
                    continue  # side indeterminate — cannot apply a per-side rule
            else:
                side = ""
            slot = (C.board_root_of(prim), rd, str(pin), role, side)  # one board's joints only (§10)
            by_slot.setdefault(slot, []).append(prim)
        for (_scope, rd, pin, role, side), prims in sorted(by_slot.items(), key=lambda kv: str(kv[0])):
            if len(prims) < 2:
                continue
            where = f"{role} on the {side} side" if side else role
            names = ", ".join(p.GetPath().name for p in prims)
            self._AddFailedCheck(
                f"{req.code}: {len(prims)} {where} claim {rd} pin '{pin}' ({names}) — one joint takes at "
                f"most one pad per side and one barrel (§6), so this yields an ROI for a joint that does "
                f"not exist.",
                at=prims[1], requirement=req)

    def _check_association_matches_geometry(self, stage: Usd.Stage, req) -> None:
        """The association must agree with the geometry: a pad sits at the pin it names (§10).

        A FAILURE, because geometry correctness is enforced, not just declaration: an association
        can be present, resolvable, and still WRONG — the claimed pin exists, the pad just sits on a
        different one. That class of defect otherwise ships invisibly: pads numbered positionally
        against sparse designators, or an association repair that swaps two connectors' claims
        pairwise, on a board that otherwise passes clean.

        Method: world-space centroids from `extent` + the prim transform. A pad fails when the pin
        it names is strictly farther away than some other pin of the same component (0.001 mm
        margin — exported pads sit at 0.000 mm from their pin, so ties never fire). Skipped
        wherever geometry is absent: a pad or pin without an authored `extent` (e.g. the
        illustrative samples), an unresolvable refdes, or a claimed pin with no located geometry —
        absence of evidence is not a finding.

        Surface-mount parts only. A through-hole lead is a bent or long mesh whose extent centroid
        does not mark where it enters the board, so the method has nothing to say about it; the
        through-hole joint's location is the barrel (BG.003, BG.010).

        A pad whose footprint overlaps its named pin's footprint (world XY) is at that pin, whatever
        else is nearby: connector pins that share one land (a USB-C A1/B12 pair) and hand-solder pad
        extensions put a second pin closer to the pad's centre without making the claim wrong. Only a
        pad clear of its named pin, with another pin nearer, is a wrong association.
        """
        xc = UsdGeom.XformCache()

        def footprint(prim):
            """World-space (centroid xy, xy bounding box) of a prim's authored extent, or None."""
            e = prim.GetAttribute("extent").Get()
            if not e:
                return None
            m = xc.GetLocalToWorldTransform(prim)
            lo, hi = Gf.Vec3d(e[0]), Gf.Vec3d(e[1])
            corners = [m.Transform(Gf.Vec3d(x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])
                       for z in (lo[2], hi[2])]
            xs, ys = [c[0] for c in corners], [c[1] for c in corners]
            c = m.Transform((lo + hi) * 0.5)
            return (c[0], c[1]), (min(xs), max(xs), min(ys), max(ys))

        def overlaps(a, b):
            return a[0] <= b[1] and b[0] <= a[1] and a[2] <= b[3] and b[2] <= a[3]

        pin_sites = {}  # component identity -> [(pin number, x, y, xy box)]
        for comp in C.iter_components(stage):
            ident = C.identity(comp)
            if ident is None or C.is_tht(comp):
                continue
            rows = []
            for p in C.pins_of(comp):
                n = C.get(p, "pcba:pin:number")
                fp = footprint(p)
                if n is not None and fp is not None:
                    rows.append((str(n), fp[0][0], fp[0][1], fp[1]))
            if len(rows) > 1:  # with one located pin there is nothing to disagree with
                pin_sites[(C.board_root_of(comp), ident)] = rows

        for prim in C.iter_meshes(stage):
            if C.role_of(prim) != "board_pad":
                continue
            rd = C.get(prim, "pcba:board:refdes")
            attr = C.board_pin_number_attr(prim)
            claim = C.get(prim, attr) if attr else None
            if not rd or claim is None:
                continue
            rows = pin_sites.get((C.board_root_of(prim), rd))
            if not rows:
                continue
            fp = footprint(prim)
            if fp is None:
                continue
            (wx, wy), pad_box = fp
            claim = str(claim)
            best_n = best_d = claim_d = None
            for n, x, y, box in rows:
                d = math.hypot(x - wx, y - wy)
                if best_d is None or d < best_d:
                    best_n, best_d = n, d
                if n == claim and (claim_d is None or d < claim_d):
                    claim_d = d
                    if overlaps(pad_box, box):
                        claim_d = 0.0  # the pad lies on its named pin; nothing nearer can contradict that
            if claim_d is None:
                continue  # claimed pin has no located geometry; existence is the resolve check's job
            if best_n != claim and claim_d > best_d + 1e-3:
                self._AddFailedCheck(
                    f"{req.code}: {C.label(prim)} claims {rd} pin '{claim}' ({claim_d:.3f} mm away) but "
                    f"sits on pin '{best_n}' ({best_d:.3f} mm) — the association must agree with the "
                    f"geometry (§10); solder placed by this claim lands on the wrong joint.",
                    at=prim, requirement=req)


# There is no BG.013 rule: `pcba:component:insertionSide` / `:solderSide` are not required. With body
# and pin meshes separated per part, the solder side is recoverable from the geometry, so the
# component-level attributes would be redundant.
