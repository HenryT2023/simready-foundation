# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
PCB USD Organization (UO) validators.

How a board USD is organized so the pipeline can discover geometry by role and
registries. Requirement prose lives in the contract: `usd_spec/pcb_usd_contract.md`
(§2 mesh role, §4 registries/manifest, §5 stage layout, §6 stage conventions,
§9 references, §10 provenance/origin).

SRF-shaped: `usd_validation_nvidia.BaseRuleChecker` subclasses. The only line that
changes on a port to SimReady Foundations is the `requirements` import below.
"""
import os
import re

import usd_validation_nvidia
from pxr import Usd, UsdGeom, UsdShade

from .. import _contract as C
import simready.foundation.tier_pcb.requirements as cap


@usd_validation_nvidia.register_rule("PCB-Stage")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_006)
class StageConventionsChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.006 — Stage conventions.

    Summary: the board stage MUST use ``metersPerUnit == 0.001`` (mm) and
        ``upAxis == Z``, with no compensating root scale/rotation. The board lies in
        the XY plane with Z as the board normal.
    Contract: usd_spec/pcb_usd_contract.md §6.
    Checks:
        - metersPerUnit == 0.001 (mm)
        - upAxis == Z
        - default prim exists and carries no compensating root scale/rotation
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_006
        if abs(UsdGeom.GetStageMetersPerUnit(stage) - 0.001) > 1e-9:
            self._AddFailedCheck("UO.006: metersPerUnit must be 0.001 (mm).", at=stage, requirement=req)
        if UsdGeom.GetStageUpAxis(stage) != UsdGeom.Tokens.z:
            self._AddFailedCheck("UO.006: upAxis must be 'Z' (board is Z-normal).", at=stage, requirement=req)
        dp = stage.GetDefaultPrim()
        if not dp:
            self._AddFailedCheck("UO.006: no defaultPrim (expected /Board).", at=stage, requirement=req)
            return
        xf = UsdGeom.Xformable(dp)
        if xf:
            bad = [o.GetOpName() for o in xf.GetOrderedXformOps()
                   if "scale" in o.GetOpName() or "rotate" in o.GetOpName()]
            if bad:
                self._AddFailedCheck(f"UO.006: default prim has compensating root xform {bad}.", at=dp, requirement=req)


@usd_validation_nvidia.register_rule("PCB-MeshRole")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_009)
class MeshRoleChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.009 — Mesh role vocabulary.

    Summary: every ``UsdGeomMesh`` MUST carry ``pcba:mesh:role``, a token from the
        contract vocabulary. The role is authoritative — prim names must not replace it.
    Contract: usd_spec/pcb_usd_contract.md §2.
    Checks:
        - every Mesh has a `pcba:mesh:role` attribute
        - its value is in the component/board role vocabulary
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_009
        # Route through C.stage_range so this rule inherits the shared traversal policy (abstract
        # `class` masters in, instance proxies out). A private Usd.PrimRange with the default
        # predicate would silently skip a board authored under a class prim.
        for prim in C.stage_range(stage):
            if not UsdGeom.Mesh(prim):
                continue
            # Read through C.get so the `pcb:` spelling also resolves.
            role = C.get(prim, "pcba:mesh:role")
            if role is None:
                self._AddFailedCheck("UO.009: Mesh missing pcba:mesh:role.", at=prim, requirement=req)
            elif role in C.DEPRECATED_MESH_ROLES:
                # Deprecated role (e.g. pkg_solder). Warn with the reason rather than failing with an
                # opaque "not in vocabulary" — assets built from some CAD libraries carry these.
                self._AddWarning(
                    f"UO.009: pcba:mesh:role '{role}' is retired — {C.DEPRECATED_MESH_ROLES[role]}.",
                    at=prim, requirement=req)
            elif role not in C.MESH_ROLES:
                self._AddFailedCheck(f"UO.009: pcba:mesh:role '{role}' not in vocabulary.", at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_001)
class BoardRootChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.001 — Default prim + discoverable board root.

    Summary: the asset MUST have a single default prim (§2 — its name is FREE), and a board-root prim
        carrying `pcba:board:*` metadata MUST be discoverable by attribute. The board root may BE the
        default prim (a bare board) or a child under a scene wrapper (a `/World` holding cameras/lights);
        the source requires discovery by attribute/semantics, not by prim structure.
    Checks:
        - stage.GetDefaultPrim() exists (MUST) and is Xformable (MUST)
        - a board-root prim carrying pcba:board:* is present (MUST)
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_001
        dp = stage.GetDefaultPrim()
        if not dp:
            self._AddFailedCheck("UO.001: no defaultPrim (the board asset must have a single default prim).",
                                 at=stage, requirement=req)
        elif not UsdGeom.Xformable(dp):
            self._AddFailedCheck(f"UO.001: default prim {C.label(dp)} is not Xformable.", at=dp, requirement=req)
        root = C.board_root(stage)
        if root is None:
            self._AddFailedCheck("UO.001: no board-root prim carrying pcba:board:* metadata found.",
                                 at=stage, requirement=req)
            return
        # pcba:board:name is a top-level (board-root) field only - flag it elsewhere.
        for prim in C.stage_range(stage):
            # Any board root may carry it - a panel has one per authored board (section 3/11), not one per stage.
            if C.is_board_root(prim) or not C.defined(prim, "pcba:board:name"):
                continue
            # A panel position is an INSTANCE of the board master, so it resolves the master's
            # `pcba:board:name` through its reference. That is not the vendor name being repeated down
            # the hierarchy - it is authored once, on the master, which is exactly what this rule wants.
            # Flagging it would give every panel one false warning per position.
            if prim.IsInstance():
                continue
            self._AddWarning(f"UO.001: pcba:board:name authored on {C.label(prim)} - it belongs only on "
                             f"the board root {C.label(root)}.", at=prim, requirement=req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_003)
class StageLayoutChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.003 — Stage layout / required geometry groups.

    Summary: the board body MUST be present as a Mesh with role ``board_substrate``.
    Contract: usd_spec/pcb_usd_contract.md §5.
    Checks:
        - at least one Mesh with role `board_substrate` exists (MUST)

    There is no THT check here ("through_hole components but no `board_hole` geometry"): `board_hole`
    prims are optional (§6) and the barrel is the required geometry, which BG.003 checks; repeating
    it here would only double-report the same condition.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_003
        roles = {C.role_of(m) for m in C.iter_meshes(stage)}
        if "board_substrate" not in roles:
            self._AddFailedCheck("UO.003: no Mesh with role 'board_substrate' (board body missing).",
                                 at=stage, requirement=req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_008)
class RegistriesChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.008 — Component registry.

    Summary: a ``pcba:board:members`` relationship SHOULD enumerate **every placed component**, so a
        consumer can index parts without a full stage traversal.
    Contract: usd_spec/pcb_usd_contract.md §3.

    Two design points:

    1. **All components, not just through-hole.** A THT-only registry would cut against §12 ("one model,
       conditional fields") and index the smaller population - a typical board carries an order of
       magnitude more SMT parts than THT. A subset is a `processClass` selection, which is what that
       attribute is for; parallel per-class registries are explicitly not wanted.
    2. **SHOULD, not MUST.** Nothing downstream depends on it, and the registry is an *index*, not a
       source of truth - `processClass` and the component prims are authoritative. A stale or
       over-inclusive registry is worse than none, because a consumer trusting it gets a confidently
       wrong answer. So its absence is a warning, and its *contents* are checked in both directions.

    Checks (all advisory):
        - if components exist, a `pcba:board:members` relationship is authored
        - every placed component appears in it (under-inclusion)
        - every target resolves to a real component prim (over-inclusion / stale targets)
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_008
        components = {c.GetPath(): c for c in C.iter_components(stage)}
        if not components:
            return
        members = set()
        found = False
        for prim in C.stage_range(stage):
            # Both spellings — the `pcb:` namespace also resolves.
            for name in ("pcba:board:members", "pcb:board:members"):
                rel = prim.GetRelationship(name)
                if rel and rel.IsDefined():
                    found = True
                    members.update(rel.GetTargets())
                    break
        if not found:
            self._AddWarning(
                f"UO.008: {len(components)} placed component(s) but no pcba:board:members registry "
                f"(SHOULD - lets a consumer index parts without a full stage traversal).",
                at=stage, requirement=req)
            return
        for path in sorted(components):
            if path not in members:
                self._AddWarning(f"UO.008: component {path} is not listed in the pcba:board:members registry.",
                                 at=stage, requirement=req)
        # Over-inclusion: a registry naming a non-component or deleted prim is actively misleading,
        # since a consumer trusting it gets a wrong answer that would otherwise validate clean.
        for path in sorted(members):
            if path not in components:
                self._AddWarning(
                    f"UO.008: pcba:board:members lists {path}, which is not a placed component "
                    f"(stale target, or a prim carrying no pcba:component:* identity).",
                    at=stage, requirement=req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_010)
class NamespaceChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.010 — pcba: namespace convention.

    Summary: authored attributes should live under one of the recognized ``pcba:``
        sub-namespaces. An unrecognized sub-namespace is almost always a typo
        (e.g. ``pcba:compontent:...``).
    Contract: usd_spec/pcb_usd_contract.md §1. Advisory only — never a hard fail.
    Checks:
        - every authored `pcb…`/`pcba…` attribute on components and role-bearing meshes uses
          a valid sub-namespace (WARNING otherwise)
        - the `pcb:` namespace is reported as deprecated (WARNING), once per prim

    The namespace is `pcba:`. The `pcb:` spelling is READ everywhere (see `_contract.resolve_attr`),
    so an asset authored with it still validates; this rule is what tells an author to rename to `pcba:`.
    """

    # Sub-namespaces the contract allows. `pcba:layer:` (layer stackup) is optional-allowed and does not
    # warn; it MUST NOT determine a *component's* side (that comes from `pcba:component:side` and mesh
    # roles) — its sanctioned use is deriving paste/pad side from the containing layer (§11.1).
    # `pcba:panel:` and `pcba:fixture:` carry the minimal panel support (§3).
    # `pcba:variance:` (§11.3) — OPTIONAL manufacturing-variance ranges the manufacturer
    # fills from process-preparation data/BOM. Never changes what the geometry means; a consumer may ignore it entirely.
    _VALID = ("pcba:component:", "pcba:mesh:", "pcba:pin:", "pcba:board:", "pcba:prov:", "pcba:layer:",
              "pcba:panel:", "pcba:fixture:", "pcba:variance:")
    # Same set under the `pcb:` namespace — recognized, but deprecated rather than "unknown".
    _VALID_LEGACY = tuple(C.LEGACY_NS + s[len(C.NS):] for s in _VALID)

    def _check(self, prim: Usd.Prim, req) -> None:
        legacy_seen = []
        for attr in prim.GetAuthoredAttributes():
            name = attr.GetName()
            if not name.startswith("pcb"):
                continue
            if name.startswith(self._VALID):
                continue
            if name.startswith(self._VALID_LEGACY):
                legacy_seen.append(name)
                continue
            self._AddWarning(f"UO.010: {C.label(prim)} attribute '{name}' is not in a valid pcba: sub-namespace.",
                             at=prim, requirement=req)
        if legacy_seen:
            self._AddWarning(
                f"UO.010: {C.label(prim)} authors {len(legacy_seen)} attribute(s) under the retired "
                f"'{C.LEGACY_NS}' namespace (e.g. '{legacy_seen[0]}') — rename to '{C.NS}'. "
                f"Still read for now; migrate when convenient.",
                at=prim, requirement=req)

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_010
        for prim in C.iter_components(stage):
            self._check(prim, req)
        for mesh in C.iter_meshes(stage):
            if C.role_of(mesh) is not None:
                self._check(mesh, req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_011)
class MaterialBindingChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.011 — Material binding on renderable component meshes.

    Summary: component (``pkg_*``) meshes should carry a bound material so they render
        with their nominal appearance. Materials are approximate at input time and the
        conformant sample is unbound, so this is advisory (WARNING), never a hard fail.
    Contract: usd_spec/pcb_usd_contract.md §2.
    Checks:
        - every Mesh with a component role has a direct material binding (WARNING otherwise)
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_011
        for mesh in C.iter_meshes(stage):
            if C.role_of(mesh) not in C.COMPONENT_ROLES:
                continue
            rel = UsdShade.MaterialBindingAPI(mesh).GetDirectBindingRel()
            if not rel or not rel.GetTargets():
                self._AddWarning(f"UO.011: component mesh {C.label(mesh)} has no bound material.",
                                 at=mesh, requirement=req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_012)
class RelativeReferencesChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.012 — Relative, self-contained references.

    Summary: references and payloads MUST use relative asset paths so the package is
        portable. Absolute filesystem paths, drive letters, and URLs break relocation.
    Contract: usd_spec/pcb_usd_contract.md §9.
    Checks:
        - the stage composes without errors: every reference/payload resolves (MUST) — a missing
          component prototype or board file fails here rather than passing vacuously
        - no reference/payload assetPath is absolute (leading '/', a Windows drive, or a
          file:/omniverse:/http(s): URL) (MUST)
    """

    _ABS = re.compile(r"^(/|[A-Za-z]:[\\/]|[A-Za-z][A-Za-z0-9+.\-]*://|file:|omniverse:|https?:)")

    @staticmethod
    def _items(list_op):
        if list_op is None:
            return []
        items = []
        for field in ("prependedItems", "appendedItems", "addedItems", "explicitItems", "orderedItems"):
            items.extend(getattr(list_op, field, None) or [])
        return items

    def _check(self, prim: Usd.Prim, key: str, kind: str, req) -> None:
        for item in self._items(prim.GetMetadata(key)):
            path = getattr(item, "assetPath", None)
            if path and self._ABS.match(path):
                self._AddFailedCheck(f"UO.012: {C.label(prim)} has absolute {kind} assetPath '{path}'.",
                                     at=prim, requirement=req)

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_012
        # A self-contained asset resolves every reference/payload it makes (§1, §4). A composition
        # error means a dependency is missing or unreadable — the board is not the board it claims
        # to be, and every rule that looks for that geometry passes vacuously. Fail it here, once
        # per distinct error, so an incomplete package can never validate clean.
        seen = set()
        for err in stage.GetCompositionErrors():
            msg = str(err).strip().splitlines()[0] if str(err).strip() else type(err).__name__
            if msg in seen:
                continue
            seen.add(msg)
            self._AddFailedCheck(f"UO.012: unresolved composition - {msg}", at=stage, requirement=req)
        for prim in C.stage_range(stage):
            self._check(prim, "references", "reference", req)
            self._check(prim, "payloads", "payload", req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_013)
class PackageManifestChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.013 — Package manifest.

    Summary: a distributed package should declare ``pcba:board:packageManifest`` (the
        package-file BOM) on the board root. Whether the asset is a distributed package
        is not detectable here, so this is advisory (WARNING).
    Contract: usd_spec/pcb_usd_contract.md §4.
    Checks:
        - default prim declares `pcba:board:packageManifest` (WARNING otherwise)
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_013
        dp = C.board_root(stage)  # board root discovered by attribute (may be under a scene wrapper)
        if not dp:
            return  # absence reported by UO.001
        if C.defined(dp, "pcba:board:packageManifest"):
            return
        if C.waived(dp, "packageManifest"):
            # A deferred manifest is a declared gap (§14), counted like every other marker rather
            # than silently accepted.
            C.add_waived(self, req, "pcba:board:packageManifest", dp)
            return
        self._AddWarning(f"UO.013: board root {C.label(dp)} does not declare pcba:board:packageManifest.",
                         at=dp, requirement=req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_014)
class OriginConventionChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.014 — Origin convention.

    Summary: the board root MUST declare ``pcba:board:originConvention`` from the
        contract vocabulary, so consumers know how board XY coordinates are anchored.
    Contract: usd_spec/pcb_usd_contract.md §11.
    Checks:
        - default prim declares `pcba:board:originConvention` (MUST)
        - its value is in ORIGIN_CONVENTIONS (MUST)
        - `datum_explicit` additionally requires `pcba:board:originPointMm` (MUST)

    Real boards frequently put zero somewhere other than a corner — a mechanical mounting hole is
    common, and the datum is sometimes outside the board outline entirely — so `datum_explicit` has
    to state where zero actually is rather than leaving a consumer to assume a bounding-box corner.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_014
        dp = C.board_root(stage)  # board root discovered by attribute
        if not dp:
            return  # absence reported by UO.001
        if not C.defined(dp, "pcba:board:originConvention"):
            if C.waived(dp, "originConvention"):
                C.add_waived(self, req, "pcba:board:originConvention", dp)
            else:
                self._AddFailedCheck(f"UO.014: board root {C.label(dp)} missing pcba:board:originConvention.",
                                     at=dp, requirement=req)
            return
        val = C.get(dp, "pcba:board:originConvention")
        if val not in C.ORIGIN_CONVENTIONS:
            self._AddFailedCheck(f"UO.014: pcba:board:originConvention '{val}' on {C.label(dp)} not in vocabulary.",
                                 at=dp, requirement=req)
            return
        if val == "datum_explicit" and not C.defined(dp, "pcba:board:originPointMm"):
            self._AddFailedCheck(
                f"UO.014: {C.label(dp)} declares originConvention 'datum_explicit' but no "
                f"pcba:board:originPointMm — the datum location is unstated.",
                at=dp, requirement=req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_015)
class ProvenanceChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.015 — Provenance.

    Summary: the board root MUST declare ``pcba:board:generatorVersion`` and
        ``pcba:board:contentHash`` (both non-empty) so an asset traces back to the tool
        and source data that produced it.
    Contract: usd_spec/pcb_usd_contract.md §10.
    Checks:
        - default prim declares non-empty `pcba:board:generatorVersion` (MUST)
        - default prim declares non-empty `pcba:board:contentHash` (MUST)
    """

    _FIELDS = ("generatorVersion", "contentHash")

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_015
        dp = C.board_root(stage)  # board root discovered by attribute
        if not dp:
            return  # absence reported by UO.001
        for leaf in self._FIELDS:
            attr = f"pcba:board:{leaf}"
            if not C.defined(dp, attr):
                if C.waived(dp, leaf):
                    C.add_waived(self, req, attr, dp)
                else:
                    self._AddFailedCheck(f"UO.015: board root {C.label(dp)} missing {attr}.",
                                         at=dp, requirement=req)
                continue
            if C.get(dp, attr) in (None, ""):
                self._AddFailedCheck(f"UO.015: {attr} is declared but empty on {C.label(dp)}.",
                                     at=dp, requirement=req)


@usd_validation_nvidia.register_rule("PCB-UsdOrganization")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_016)
class FileNamingChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.016 — File naming (§2, SHOULD).

    Summary: every USD file in the asset (the root layer and each referenced/payloaded/sublayer file)
        SHOULD use clean ASCII names with no spaces and no parentheses — those break USD asset
        references and tooling.
    Advisory (WARNING), one finding per offending file.
    """

    _BAD = re.compile(r"[ ()]")

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_016
        seen = set()
        for layer in stage.GetUsedLayers():
            path = layer.realPath  # empty for anonymous / in-memory layers
            if not path:
                continue
            base = os.path.basename(path)
            if base in seen:
                continue
            seen.add(base)
            if self._BAD.search(base) or not base.isascii():
                self._AddWarning(
                    f"UO.016: file name '{base}' has spaces/parentheses/non-ASCII "
                    f"(breaks USD references - use clean ASCII names).",
                    at=stage, requirement=req)


@usd_validation_nvidia.register_rule("PCB-Stage")
@usd_validation_nvidia.register_requirements(cap.UsdOrganizationRequirements.UO_017)
class RoleMaterialConsistencyChecker(usd_validation_nvidia.BaseRuleChecker):
    """UO.017 — Role/material consistency.

    A mesh's `pcba:mesh:role` must agree with the class of its bound material — a `board_copper` mesh bound
    to a silkscreen material is a defect (silkscreen mis-tagged as copper, for instance).

    Keyed on the material's **class/family, not the specific material**, so multiple
    materials can share a role (standard `SolderPaste` and a burnt-solder defect variant both count as
    solder). Only cross-class contradictions fail. Meshes whose role is ambiguous (`pkg_body`/`pkg_lid`/
    `pkg_marking`), whose material is unrecognized, or which have no bound material are skipped — never
    failed — to avoid false positives.
    """

    def CheckStage(self, stage: Usd.Stage) -> None:
        req = cap.UsdOrganizationRequirements.UO_017
        for prim in C.iter_meshes(stage):
            role = C.role_of(prim)
            expected = C.ROLE_MATCLASS.get(role)
            if expected is None:
                continue
            # An authored matClass on a role whose class is derived must agree with the derivation (section 9).
            authored = C.get(prim, "pcba:mesh:matClass")
            if authored is not None and authored != expected:
                self._AddFailedCheck(
                    f"UO.017: {role} mesh {C.label(prim)} authors pcba:mesh:matClass '{authored}'; the role "
                    f"derives '{expected}'.",
                    at=prim, requirement=req)
            # The material *effectively* bound in each placed context - binding strength and inheritance
            # resolved, prototype meshes evaluated under their placements.
            for matname in C.effective_material_names(prim):
                actual = C.material_class(matname)
                if actual is None or actual == expected:
                    continue
                self._AddFailedCheck(
                    f"UO.017: {role} mesh {C.label(prim)} is bound to material '{matname}' "
                    f"({actual}); role implies '{expected}'.",
                    at=prim, requirement=req)
