# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
PCB Component Identity (CI) validators — `pcb_usd_contract.md` §1.

Identity / BOM fields on each placed component prim (bearing `pcba:component:refdes`).
One rule per requirement code, so an exporter gets a precise, per-code report.

Severity model:
  - a `MUST` field absent or out of vocabulary  → FAILURE
  - a `MUST (null-ok)` field not declared        → FAILURE; declared-but-empty is OK
  - a `pcba:prov:<attr> = "not_yet_available"` marker downgrades a missing field → WARNING

SRF-shaped: the only line that changes on a port is the `requirements` import.
"""
import usd_validation_nvidia
from pxr import Usd

from .. import _contract as C
import simready.foundation.tier_pcb.requirements as cap


def _require(checker, prim, attr_leaf, req, vocab=None, allow_empty=False):
    """Shared MUST check for a `pcba:component:<attr_leaf>` field, honoring the prov waiver."""
    attr = f"pcba:component:{attr_leaf}"
    if not C.defined(prim, attr):
        if C.waived(prim, attr_leaf):
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


@usd_validation_nvidia.register_rule("PCB-ComponentIdentity")
@usd_validation_nvidia.register_requirements(cap.ComponentIdentityRequirements.CI_001)
class RefdesChecker(usd_validation_nvidia.BaseRuleChecker):
    """CI.001 — Component identity. Every placed component is addressable, and refdes is unique.

    Contract: pcb_usd_contract.md §8 / §8.1.
      - electrical parts MUST carry a non-empty `pcba:component:refdes`
      - fiducial / mechanical parts SHOULD carry one (mechanical parts
        routinely ship without a refdes and fiducials usually but not always have one) — when absent
        they MUST carry `pcba:component:instanceId` instead, so the placement stays addressable
      - every authored refdes is unique **within one board**. Uniqueness is NOT checked across a
        panel: the same refdes legitimately repeats once per panel position, so a stage-wide check
        would fail every panel. `iter_components` already dedupes instance copies to their authored
        definition, which is what scopes this to the board.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentIdentityRequirements.CI_001
        seen = {}
        count = 0
        for prim in C.iter_components(stage):
            count += 1
            rd = C.get(prim, "pcba:component:refdes")
            if rd in (None, ""):
                # No refdes. Electrical parts must have one; the two non-electrical classes may
                # substitute a stable instanceId.
                if C.is_electrical(prim):
                    if C.waived(prim, "refdes"):
                        C.add_waived(self, req, "pcba:component:refdes", prim)
                    else:
                        self._AddFailedCheck(
                            f"CI.001: component {prim.GetPath()} has no pcba:component:refdes.",
                            at=prim, requirement=req)
                elif C.instance_id(prim) in (None, ""):
                    self._AddFailedCheck(
                        f"CI.001: {prim.GetPath()} ({C.process_class(prim)}) has neither "
                        f"pcba:component:refdes nor pcba:component:instanceId — the placement is not "
                        f"addressable.", at=prim, requirement=req)
                continue
            # Unique within one board (§8): key on the containing board root, so a panel that
            # carries two authored boards (or an unused library master beside its placements) is
            # never read as one board with duplicated parts.
            key = (C.board_root_of(prim), rd)
            if key in seen:
                self._AddFailedCheck(f"CI.001: duplicate refdes '{rd}' ({prim.GetPath()} and {seen[key]}).",
                                     at=prim, requirement=req)
            else:
                seen[key] = prim.GetPath()
        if count == 0:
            self._AddFailedCheck("CI.001: no components found on stage (no prim carries "
                                 "pcba:component:refdes, :processClass, or :instanceId).",
                                 at=stage, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentIdentity")
@usd_validation_nvidia.register_requirements(cap.ComponentIdentityRequirements.CI_002)
class ComponentTypeChecker(usd_validation_nvidia.BaseRuleChecker):
    """CI.002 — Component type. `pcba:component:type` present and in vocabulary (not derived from refdes)."""

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentIdentityRequirements.CI_002
        for prim in C.iter_components(stage, electrical_only=True):
            _require(self, prim, "type", req, vocab=C.COMPONENT_TYPES)


@usd_validation_nvidia.register_rule("PCB-ComponentIdentity")
@usd_validation_nvidia.register_requirements(cap.ComponentIdentityRequirements.CI_003)
class ProcessClassChecker(usd_validation_nvidia.BaseRuleChecker):
    """CI.003 — Process class. `pcba:component:processClass` present and in vocabulary (selects SMT/THT).

    Mixed-technology parts: a component whose terminals combine mounting
    technologies declares `processClass = "Mixed"` and lists the real classes in `pcba:component:processClasses`
    (each a member of the per-mount vocabulary, e.g. `["through_hole", "SMT"]`).

    `processClass` states HOW a part is mounted. Package families (BGA, LGA,
    QFN, …) are not mount methods and belong in `packageType`. The superseded tokens
    (`SMT_leaded` / `SMT_leadless` / `BGA`) are accepted with a WARNING naming the replacement.
    """

    def _deprecated(self, prim, val, req) -> bool:
        """Warn (not fail) on a superseded token. True if `val` was one."""
        repl = C.DEPRECATED_PROCESS_CLASSES.get(val)
        if repl is None:
            return False
        self._AddWarning(
            f"CI.003: {C.label(prim)} uses superseded processClass '{val}' — use '{repl}' "
            f"(a package family is not a mount method; put it in pcba:component:packageType).",
            at=prim, requirement=req)
        return True

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentIdentityRequirements.CI_003
        for prim in C.iter_components(stage):
            val = C.get(prim, "pcba:component:processClass")
            if not self._deprecated(prim, val, req):
                _require(self, prim, "processClass", req, vocab=C.PROCESS_CLASSES)
            if val != "Mixed":
                continue
            # Mixed → require processClasses listing the actual mount technologies.
            classes = C.get(prim, "pcba:component:processClasses")
            if not classes:
                self._AddFailedCheck(
                    f"CI.003: {C.label(prim)} has processClass 'Mixed' but no pcba:component:processClasses list.",
                    at=prim, requirement=req)
                continue
            stale = [c for c in classes if c in C.DEPRECATED_PROCESS_CLASSES]
            if stale:
                self._AddWarning(
                    f"CI.003: {C.label(prim)} pcba:component:processClasses {stale} use superseded tokens — "
                    f"map to {sorted({C.DEPRECATED_PROCESS_CLASSES[c] for c in stale})}.",
                    at=prim, requirement=req)
            bad = [c for c in classes
                   if c not in C.MOUNT_CLASSES and c not in C.DEPRECATED_PROCESS_CLASSES]
            if bad:
                self._AddFailedCheck(
                    f"CI.003: {C.label(prim)} pcba:component:processClasses {list(bad)} not in the mount vocabulary.",
                    at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentIdentity")
@usd_validation_nvidia.register_requirements(cap.ComponentIdentityRequirements.CI_004)
class PackageTypeChecker(usd_validation_nvidia.BaseRuleChecker):
    """CI.004 — Package type. `pcba:component:packageType` carries the JEDEC package designation
    (e.g. QFN-48, 0402, DIP-8, TO-99).

    SHOULD, not MUST: most parts have a JEDEC designation but not all do,
    so an absent packageType is a WARNING. A *declared but empty* value is still a failure — that's an
    exporter discarding a field it had. The value is a free string, deliberately not an enum: the package
    space is open-ended (BGA, LGA, and endless vendor-specific bodies).
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentIdentityRequirements.CI_004
        attr = "pcba:component:packageType"
        for prim in C.iter_components(stage, electrical_only=True):
            if not C.defined(prim, attr):
                self._AddWarning(
                    f"CI.004: {C.label(prim)} has no {attr} (JEDEC package designation). "
                    f"SHOULD be authored where the part has one.", at=prim, requirement=req)
            elif C.get(prim, attr) in (None, ""):
                self._AddFailedCheck(f"CI.004: {attr} is declared but empty on {C.label(prim)}.",
                                     at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-ComponentIdentity")
@usd_validation_nvidia.register_requirements(cap.ComponentIdentityRequirements.CI_005)
class FootprintIdChecker(usd_validation_nvidia.BaseRuleChecker):
    """CI.005 — Footprint id. `pcba:component:footprintId` present and non-empty (pad/hole land-pattern pointer)."""

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentIdentityRequirements.CI_005
        for prim in C.iter_components(stage, electrical_only=True):
            _require(self, prim, "footprintId", req)


@usd_validation_nvidia.register_rule("PCB-ComponentIdentity")
@usd_validation_nvidia.register_requirements(cap.ComponentIdentityRequirements.CI_006)
class PartIdentityChecker(usd_validation_nvidia.BaseRuleChecker):
    """CI.006 — Part identity, checked as TWO independent groups.

    `mpn`/`manufacturer` and `value`/`tolerance` have different authors and different lifecycles, so
    they are validated separately:

      - **`value` + `tolerance`** — the *electrical requirement*, set by the designer.
      - **`mpn` + `manufacturer`** — the *manufacturer's* part identity. Frequently not fixed at design
        time: many programs place an internal part number that maps to a bucket of approved
        equivalents, and operations picks the actual part later.
      - **`customerPartNumber`** — the board owner's internal number (NVPN / WPN / IPN). Often the only
        identity present at design time. OPTIONAL: absence is not reported.

    Contract: pcb_usd_contract.md §8 ("declare-always, populate-when-known"). The fields must be
    authored, but may be empty when genuinely inapplicable — so this checks declaration, not
    population. Reporting stays per-group so a partner sees *which* identity is missing.
    """

    _GROUPS = (
        ("electrical requirement", ("value", "tolerance")),
        ("manufacturer part identity", ("mpn", "manufacturer")),
    )

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.ComponentIdentityRequirements.CI_006
        for prim in C.iter_components(stage, electrical_only=True):
            for _group, fields in self._GROUPS:
                for leaf in fields:
                    _require(self, prim, leaf, req, allow_empty=True)
            # customerPartNumber is optional — only flag a declared-but-empty value, which means the
            # exporter had the field and discarded its content.
            cpn = "pcba:component:customerPartNumber"
            if C.defined(prim, cpn) and C.get(prim, cpn) == "":
                self._AddWarning(f"CI.006: {cpn} is declared but empty on {C.label(prim)}.",
                                 at=prim, requirement=req)
