# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Shared vocabulary and stage-traversal helpers for the PCB → USD input-contract
validators.

Pure OpenUSD (`pxr`) — no dependency on `usd_validation_nvidia` or the requirement
registry — so this module ports to SimReady Foundations **unchanged** (only the
per-capability rule files carry the one-line `requirements` import seam).

All vocabularies and attribute names trace to `usd_spec/pcb_usd_contract.md`.
"""
from pxr import Tf, Usd, UsdGeom

# --------------------------------------------------------------------------- #
# Controlled vocabularies (pcb_usd_contract.md)
# --------------------------------------------------------------------------- #
# `processClass` = HOW A PART IS MOUNTED — nothing else. There are only two real assembly methods,
# surface-mount and through-hole. `press_fit` is a third mount style; `mechanical`/`fiducial` are
# non-electrical placements. Package FAMILIES (BGA, LGA, QFN, …) are not mount methods — they live in
# `pcba:component:packageType` as a JEDEC string, which is open-ended by nature.
PROCESS_CLASSES = {
    "SMT", "through_hole", "press_fit", "mechanical", "fiducial",
    "Mixed",  # mixed-technology part; the real classes go in `processClasses`
}
THT_PROCESS_CLASSES = {"through_hole", "press_fit"}
# Valid members of `pcba:component:processClasses` (the per-mount-tech classes a `Mixed` part combines).
MOUNT_CLASSES = {"SMT", "through_hole", "press_fit"}

# Superseded tokens → their replacement. Each is still accepted, so an asset authored with one still
# validates, but every use raises a WARNING naming the replacement. `BGA` collapses to `SMT`: a BGA is
# surface-mounted; the package goes in `packageType`.
DEPRECATED_PROCESS_CLASSES = {"SMT_leaded": "SMT", "SMT_leadless": "SMT", "BGA": "SMT"}

COMPONENT_TYPES = {
    "resistor", "capacitor", "inductor", "led", "diode", "transistor",
    "connector", "crystal", "switch", "ic", "other",
}

COMPONENT_ROLES = {"pkg_body", "pkg_lead", "pkg_lid", "pkg_marking"}
# `pkg_solder` is not a role. A delivered component carries no solder on it — solder joints are
# generated downstream, which is why there is no `board_solder` either. Some CAD libraries ship parts
# with solder pre-attached to the leads for visual fidelity; that must be stripped on export.
# Listed here so the rule can emit a targeted WARNING instead of an opaque "not in vocabulary" failure.
DEPRECATED_MESH_ROLES = {
    "pkg_solder": "solder is generated downstream — strip pre-attached solder from package meshes",
}
BOARD_ROLES = {
    "board_substrate", "board_copper", "board_mask", "board_pad",
    "board_paste", "board_hole", "board_barrel",
    "board_fiducial",  # fiducial marker geometry gets its own role
    "board_silk",      # silkscreen geometry gets its own role. The token is `board_silk`, not
                       # `board_silkscreen`.
    "board_testpoint", # exposed copper placed for electrical test. Not a component attachment pad
                       # (no joint derives from it), tagged exactly from an explicit CAD usage
                       # attribute. Tooling/mounting pads stay `board_copper`.
    "board_misc",      # the sanctioned escape hatch for a layer class with no §9 token -
                       # a generic "other" layer, a dielectric layer. Deliberately absent from
                       # ROLE_MATCLASS, so UO.017's role<->material 1-to-1 rule skips it: its material
                       # is undetermined by definition. NOT a dumping ground - a standalone mask layer
                       # is `board_mask` and a conductive plane is `board_copper`.
}
# Tooling the board or panel is mounted INTO - not part of the fabricated board.
# `board_*` means "part of the PCBA"; a carrier is a fixture that carries one or more
# boards through an assembly step, so it gets its own family. Which step it serves is
# `pcba:fixture:process` - a line may use different carriers for wave solder, reflow, test.
FIXTURE_ROLES = {"fixture_carrier"}

MESH_ROLES = COMPONENT_ROLES | BOARD_ROLES | FIXTURE_ROLES  # no board_solder — solder is downstream-generated

# Roles whose material is NOT implied by the role, so `matClass` must be authored explicitly (CG.012).
# `pkg_*` because a body may be plastic or ceramic; `fixture_*` because a carrier may be machined
# aluminium or a composite like Durostone.
MATCLASS_REQUIRED_ROLES = COMPONENT_ROLES | FIXTURE_ROLES

SIDES = {"top", "bottom"}
ANCHORS = {"body_centroid", "pin1", "footprint_origin", "mesh_origin"}
POLARITY_TYPES = {"dot", "notch", "bevel", "band", "plus", "text", "asymmetric"}
FINISHES = {"matte", "gloss", "metallic", "other"}
MATERIAL_CLASSES = {"plastic", "metal", "ceramic", "solder", "other"}
MESH_MAT_CLASSES = {"plastic", "metal", "ceramic", "solder", "mask", "copper", "silkscreen", "other"}
CROSS_SECTIONS = {"circular", "rectangular", "other"}
# Optional per-pin terminal form. Describes the physical kind of terminal; lets downstream pick the
# applicable solder-defect classes. OPTIONAL — validated only when authored. The vocabulary covers the
# lead forms that process-preparation tooling distinguishes. Notes: `pressFit` describes the terminal FORM —
# whether it also takes solder is `pcba:pin:solderable`, and the mount method stays `processClass`.
# `mixed` (a part whose pins differ in form) requires the actual forms in `pcba:component:terminalTypes`,
# mirroring `processClass = Mixed` -> `processClasses`. An "undefined" source value maps to NO token authored.
TERMINAL_TYPES = {
    "endTerminal", "gullwing", "jLead", "throughHolePin", "solderBall",
    "lLead", "cLead", "sideConcave", "cornerConcave", "flatInsulated",
    "qfn", "lcc", "lga", "solderColumn", "capae",
    "axial", "radial", "inline", "wire", "pressFit", "mixed", "otherThroughHole",
}
# Valid members of `pcba:pin:terminalTypes` (the forms a `mixed` part combines) — anything but `mixed`.
TERMINAL_TYPE_MEMBERS = TERMINAL_TYPES - {"mixed"}
SOLDER_LAYERS = {"top", "bottom"}
# `mounting_hole` / `datum_explicit`: real boards frequently put zero somewhere
# other than a corner — a mechanical mounting hole is common, and the datum is sometimes outside the
# board outline entirely. `datum_explicit` requires `pcba:board:originPointMm` to state where it is.
ORIGIN_CONVENTIONS = {"cad_bbox_lower_left", "fiducial_f1", "mounting_hole", "datum_explicit", "unspecified"}

# --------------------------------------------------------------------------- #
# Role ↔ material consistency (UO.017)
# --------------------------------------------------------------------------- #
# The material class a role implies. Only roles whose material is determined are listed; ambiguous
# component roles (pkg_body/pkg_lid/pkg_marking — could be plastic/ceramic/metal) are omitted → skipped.
ROLE_MATCLASS = {
    # `board_hole` deliberately absent: a hole is an absence of material, so no class may be
    # derived for it — the copper is the barrel. The role is optional
    # bookkeeping (§6); a hole prim carries no derived class and UO.017 skips it.
    "board_copper": "copper", "board_pad": "copper", "board_barrel": "copper", "board_testpoint": "copper",
    "board_fiducial": "copper", "board_mask": "mask", "board_silk": "silkscreen",
    "board_paste": "solder", "board_substrate": "other",
    "pkg_lead": "metal",
}

# Known exporter material names → class. Unknown names fall through to a substring guess, then to None
# (skipped, never failed) — so defect variants of a known family (e.g. "BurntSolderPaste" → solder) still
# match by class, and genuinely-unrecognized materials don't produce false positives.
_MATERIAL_CLASS_EXACT = {
    "Copper": "copper", "Pad": "copper", "Drill": "copper",
    "SolderMask": "mask", "SilkScreen": "silkscreen", "SolderPaste": "solder",
    "Substrate": "other", "PackageLead": "metal",
    # PackageBody, Misc: intentionally unmapped (ambiguous) → skipped
}
_MATERIAL_CLASS_SUBSTR = (
    ("silk", "silkscreen"), ("mask", "mask"), ("paste", "solder"), ("solder", "solder"),
    ("copper", "copper"), ("substrate", "other"), ("laminate", "other"),
)


def material_class(name: str):
    """The material class of a bound material by name, or None if unrecognized (→ skip, don't fail)."""
    if name in _MATERIAL_CLASS_EXACT:
        return _MATERIAL_CLASS_EXACT[name]
    low = name.lower()
    for key, cls in _MATERIAL_CLASS_SUBSTR:
        if key in low:
            return cls
    return None


# --------------------------------------------------------------------------- #
# Traversal (instance-proxy aware — component geometry usually lives in a
# referenced, instanceable prototype)
# --------------------------------------------------------------------------- #
# Active + defined + loaded, but *including* ABSTRACT (`class`) prims. This is
# `Usd.PrimDefaultPredicate` minus its `!PrimIsAbstract` term. Used by BOTH traversals below - see
# `stage_range` for why, and note that `UsdPrim.IsAbstract()` is true for a prim *or any ancestor*
# being a class, so under a `class` master the whole subtree is abstract, not just its root.
AUTHORED_PRIMS = Usd.PrimIsActive & Usd.PrimIsDefined & Usd.PrimIsLoaded


def _range(prim: Usd.Prim):
    """Descendants of `prim`, through instance proxies AND through abstract (`class`) prims.

    Both terms matter. Proxies, because a component's pins usually live in a referenced, instanceable
    package prototype. Abstract, because on a panel whose board master is a `class`, every component
    and every pin under it is abstract too, and the default predicate prunes the lot — the pin rules
    (CG.007) would then silently skip every pin on the panel while reporting them on the bare board.
    """
    return Usd.PrimRange(prim, Usd.TraverseInstanceProxies(AUTHORED_PRIMS))


_MEMO_STAGE = [None]      # the stage the tables describe, held so its identity cannot be recycled
_MEMO_LISTENER = [None]   # Tf.Notice listener that clears the tables when that stage changes
_MEMO = {"spec": {}, "scope": {}, "binding": {}, "walk": {}}


def _clear_memo():
    for t in _MEMO.values():
        t.clear()


def _on_stage_changed(notice, sender):
    # Any edit to the memoized stage - an attribute, a binding's strength, a new prim - invalidates
    # everything derived from it. Validation itself never edits the stage, so within a run this
    # never fires and the tables live for the whole run; across a validate -> repair -> revalidate
    # cycle on one open stage it fires on the repair and the next run recomputes.
    _clear_memo()


def _memo(stage: Usd.Stage, table: str):
    """Per-stage memo tables. Every rule re-walks the stage, and every visit asks the same identity
    questions about the same prims; on a production board those redundant attribute lookups dominate
    the run time. The de-duplicated walk is a property of the
    stage's *current contents*, so it is computed once and replayed until the stage changes.

    Lifetime: keyed by stage object identity (the object is held, so its id cannot be reused by a
    later stage), and invalidated by `Usd.Notice.ObjectsChanged` from that stage. A different or
    re-opened stage starts clean."""
    if _MEMO_STAGE[0] is not stage:
        if _MEMO_LISTENER[0] is not None:
            _MEMO_LISTENER[0].Revoke()
        _MEMO_STAGE[0] = stage
        _MEMO_LISTENER[0] = Tf.Notice.Register(Usd.Notice.ObjectsChanged, _on_stage_changed, stage)
        _clear_memo()
    return _MEMO[table]


def _spec_key(prim: Usd.Prim):
    """Ordered (layer, path) spec stack of `prim`; for a prototype root, one instance's stack with the
    instance's own placement spec(s) stripped (the leading specs at the instance's own leaf name)."""
    table = _memo(prim.GetStage(), "spec")
    key = str(prim.GetPath())
    if key in table:
        return table[key]
    table[key] = value = _spec_key_uncached(prim)
    return value


def _spec_key_uncached(prim: Usd.Prim):
    if prim.IsPrototype():
        instances = prim.GetInstances()
        if not instances:
            return ("proto", str(prim.GetPath()))
        inst = instances[0]
        specs = [(sp.layer.identifier, str(sp.path)) for sp in inst.GetPrimStack()]
        name = inst.GetPath().name
        while specs and specs[0][1].rsplit("/", 1)[-1] == name:
            specs.pop(0)
        return tuple(specs) or ("proto", str(prim.GetPath()))
    specs = tuple((sp.layer.identifier, str(sp.path)) for sp in prim.GetPrimStack())
    return specs or ("path", str(prim.GetPath()))


def _content_key(prim: Usd.Prim):
    """Composed-identity key for de-duplicating the walk: **(board scope, spec stack)**.

    Two prims with equal spec stacks compose identically - every opinion, at every strength - so
    validating one validates the other *for intrinsic properties*. But the contract's identity and
    association checks are scoped to a board (section 8, section 10), and a prim that is intrinsically
    identical in two boards is still two facts: the unchanged `U7` inside a library master and inside a
    production master whose pad claims pin 99 must both be present, or the production board loses
    the component that proves its pad wrong. So the key carries the board scope:
    identical *boards* (a `class` master and its instances' prototype) still collapse to one visit,
    while identical content in distinct boards is visited once per board. Only prims that carry
    board-scoped identity take the scope (`_has_board_identity`); intrinsic geometry de-duplicates by
    content alone.
    """
    return (board_root_of(prim) if _has_board_identity(prim) else None, _spec_key(prim))


def _has_board_identity(prim: Usd.Prim) -> bool:
    """True for prims whose checks aggregate per board: components (`pcba:component:*`) and board
    sites, roots and registries (`pcba:board:*` attributes *or relationships* - a registry prim carries
    only `rel pcba:board:members`). Intrinsic geometry (a package mesh, a pin) carries neither and is
    de-duplicated by content alone, so a component master authored outside any board and the
    prototype its placements share are still one visit, not two."""
    return (any(has_attr(prim, m) for m in _COMPONENT_MARKERS)
            or any(has_attr(prim, m) for m in _BOARD_ROOT_MARKERS)
            or any(has_attr(prim, a) for a in _SITE_MARKERS)
            or bool(prim.GetRelationship("pcba:board:members")))


# Board-site identity: the attributes a pad/barrel/paste prim carries that make it a fact about one board.
_SITE_MARKERS = ("pcba:board:refdes", "pcba:board:componentPinNumber", "pcba:board:padNumber",
                 "pcba:board:occupied", "pcba:prov:refdes", "pcba:prov:occupied", "pcba:prov:padNumber")


def stage_range(stage: Usd.Stage):
    """Every distinct composed definition exactly once: all authored, non-instanced prims in the
    stage (abstract `class` prims included, the pseudo-root excluded), then every prototype —
    de-duplicated by composed identity (`_content_key`).

    Why this shape:

    1. **Instance proxies are NOT traversed.** A panel places the same board many times via
       instancing (StepRepeats); the board is *authored once*. Validating every placed copy would
       multiply findings and read identical refdes as duplicates.
    2. **Abstract (`class`) prims ARE traversed, wherever they sit.** The master a panel instances
       is very often a `class`: some process-preparation tools author
       `/World/_class_Boards/PCA_<board>` and reference it from each step-repeat. Under
       `Usd.PrimDefaultPredicate` that master is pruned as abstract, and since (1) already skips
       the placements, the board becomes invisible from *both* directions — such a panel would
       validate as carrier-only, every finding false. The walk uses
       `stage.Traverse`, so a master beside the board (outside the default prim) is reached and
       the pseudo-root is not. Sample asset: `samples/panel_class_master.usda`.
    3. **Prototypes ARE traversed.** Skipping proxies alone would hide two kinds of authored
       definition: package meshes inside a component's referenced prototype (an invalid role on a
       `pkg_body` would pass), and a board placed on a panel by *referencing its file* per position
       (§3 allows it; there is no in-stage master). A prototype is USD's own canonical composed
       content for its instances — the only place an instance's *actual* values (reference order,
       local overrides, strength) can be read.
    4. **De-duplication is by composed identity, not by heuristics about arcs.** A class master and
       its instances' prototype have identical spec stacks and are visited once; an overlay that
       changes any opinion produces a different stack and is visited on its own. Board-scoped
       checks (refdes uniqueness, site association) then key on `board_root_of`, so two authored
       boards in one stage never share an identity space.
    """
    table = _memo(stage, "walk")
    paths = table.get("paths")
    if paths is None:
        paths, equiv, key_of = [], {}, {}

        def visit(prim):
            key = _content_key(prim)
            key_of[str(prim.GetPath())] = key
            members = equiv.setdefault(key, [])
            members.append(prim.GetPath())
            if len(members) == 1:
                paths.append(prim.GetPath())

        for prim in stage.Traverse(AUTHORED_PRIMS):
            visit(prim)
        for proto in stage.GetPrototypes():
            for prim in Usd.PrimRange(proto, AUTHORED_PRIMS):
                visit(prim)
        # `equiv` lets a context-sensitive check (UO.017's effective material) evaluate every
        # placement of content the walk de-duplicated: the class mesh that won and the prototype
        # mesh it stood in for are one content, but their placements are not.
        table["paths"], table["equiv"], table["key_of"] = paths, equiv, key_of
    for path in paths:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            yield prim


def equivalent_prims(prim: Usd.Prim):
    """`prim` plus every prim the walk de-duplicated into it (same content key), as prims."""
    stage = prim.GetStage()
    table = _memo(stage, "walk")
    if "paths" not in table:
        for _ in stage_range(stage):  # build the tables
            pass
    key = table["key_of"].get(str(prim.GetPath()))
    members = table["equiv"].get(key) if key is not None else None
    out = []
    for path in (members or [prim.GetPath()]):
        p = stage.GetPrimAtPath(path)
        if p and p.IsValid():
            out.append(p)
    return out or [prim]


def _dedup_key(prim: Usd.Prim) -> str:
    """A stable key that collapses panel/board instance copies to their one authored definition.

    On a panel the same board (and its components/meshes) is instanced many times; every copy is an
    instance proxy of one prototype prim. Validating each copy would multiply findings and invent
    duplicate refdes. Keying on the prototype path (for proxies) counts each authored prim once.
    """
    if prim.IsInstanceProxy():
        return str(prim.GetPrimInPrototype().GetPath())
    return str(prim.GetPath())


# A placed component is discovered by ANY of these. `refdes` alone is NOT sufficient: mechanical parts
# routinely ship without one (a mounting hole is often just a CAD symbol name) and fiducials usually but
# not always carry one — exactly the classes §8.1 exempts from the refdes MUST. Discovering by refdes
# alone would leave those parts invisible to every rule, passing by never being checked.
_COMPONENT_MARKERS = (
    "pcba:component:refdes",
    "pcba:component:processClass",
    "pcba:component:instanceId",
)


def iter_components(stage: Usd.Stage, electrical_only: bool = False):
    """Every authored component prim, deduped across instance copies.

    A component is any prim bearing `pcba:component:refdes`, `pcba:component:processClass`, or
    `pcba:component:instanceId` (§8.1 discovery note) — so a refdes-less fiducial or mechanical part is
    still found and still validated against its reduced requirement set.

    `electrical_only=True` skips fiducials and mechanical parts:
    `process_class ∈ {fiducial, mechanical}` are exempt from the electrical-component MUSTs (type,
    packageType, footprintId, pinCount, appearance, anchor, height, …) — they carry only an identity
    (`refdes` or `instanceId`) + `processClass` + `pcba:mesh:role` + `side`. Rules that impose those
    MUSTs iterate with this flag.
    """
    seen = set()
    for prim in stage_range(stage):
        if any(has_attr(prim, m) for m in _COMPONENT_MARKERS):
            key = _dedup_key(prim)
            if key in seen:
                continue
            seen.add(key)
            if electrical_only and not is_electrical(prim):
                continue
            yield prim


def iter_meshes(stage: Usd.Stage):
    """Every authored Mesh, deduped across instance copies."""
    seen = set()
    for prim in stage_range(stage):
        if UsdGeom.Mesh(prim):
            key = _dedup_key(prim)
            if key not in seen:
                seen.add(key)
                yield prim


# `pcba:board:name` is deliberately NOT a marker: it is optional and belongs on a board root, but it
# does not make one. Counting it would turn any prim that (mis)carries it into a board root, and UO.001
# could never report the misplaced name it exists to catch.
_BOARD_ROOT_MARKERS = (
    "pcba:board:thicknessMm", "pcba:board:originConvention", "pcba:board:generatorVersion",
    "pcba:board:contentHash", "pcba:board:packageManifest", "pcba:board:variant",
    "pcba:board:partNumber",  # in BOM-driven organizations this is the board's real identity
)


def board_root(stage: Usd.Stage):
    """The board-root prim — discovered by `pcba:board:*` root metadata, NOT assumed to be the default prim.

    The requirements source demands discovery by attribute/semantics, not prim structure; the board may
    sit under a scene wrapper (e.g. a `/World` root holding cameras/lights). Returns the first authored
    prim carrying a board-root marker, or None if the asset carries no board-root metadata at all.
    """
    for prim in stage_range(stage):
        if any(has_attr(prim, m) for m in _BOARD_ROOT_MARKERS):
            return prim
    return None


def is_board_root(prim: Usd.Prim) -> bool:
    """True when `prim` carries `pcba:board:*` root metadata (a panel has one per authored board)."""
    return any(has_attr(prim, m) for m in _BOARD_ROOT_MARKERS)


def board_root_prim(prim: Usd.Prim):
    """Nearest ancestor-or-self that is a board root, or the prototype root for content inside a
    prototype (a prototype root exposes no markers of its own). None outside any board."""
    p = prim
    while p and p.IsValid() and not p.IsPseudoRoot():
        if p.IsPrototype() or is_board_root(p):
            return p
        p = p.GetParent()
    return None


def board_root_of(prim: Usd.Prim):
    """The board this prim belongs to, as a hashable scope key - for checks the contract scopes
    *within one board* (section 8 refdes uniqueness, section 10 association resolution), never across
    a panel.

    The key is the root's composed identity (`_spec_key`), not its path: a `class` master and the
    prototype its instances share are the same board and must share one identity space, while two
    masters of the same file (a library copy beside a production copy) are two boards. None where no
    board root is found (fixture-only content).
    """
    table = _memo(prim.GetStage(), "scope")
    key = str(prim.GetPath())
    if key in table:
        return table[key]
    if prim.IsPrototype() or is_board_root(prim):
        value = _spec_key(prim)
    else:
        parent = prim.GetParent()
        value = board_root_of(parent) if parent and parent.IsValid() and not parent.IsPseudoRoot() else None
    table[key] = value
    return value


def component_meshes(component: Usd.Prim):
    """The component's own package meshes (pkg_* role), deduped; may live in a referenced prototype."""
    meshes, seen = [], set()
    for p in _range(component):
        if p != component and UsdGeom.Mesh(p) and role_of(p) in COMPONENT_ROLES:
            key = _dedup_key(p)
            if key not in seen:
                seen.add(key)
                meshes.append(p)
    return meshes


def pins_of(component: Usd.Prim):
    """Pin prims of a component (bear `pcba:pin:number`; may live in the prototype), deduped."""
    pins, seen = [], set()
    for p in _range(component):
        if p != component and has_attr(p, "pcba:pin:number"):
            key = _dedup_key(p)
            if key not in seen:
                seen.add(key)
                pins.append(p)
    return pins


# --------------------------------------------------------------------------- #
# Attribute access (both namespace spellings)
# --------------------------------------------------------------------------- #
# The namespace is `pcba:`: the asset is a PCB *assembly*, and the namespace says so. The shorter
# `pcb:` spelling is also READ — every read below falls back to it — and UO.010 reports its use as a
# warning asking for `pcba:`. Resolution is `pcba:` first: if a prim carries both, the `pcba:`
# spelling wins.
NS = "pcba:"
LEGACY_NS = "pcb:"


def _legacy(attr: str) -> str:
    """The `pcb:` spelling of a `pcba:*` attribute name."""
    return LEGACY_NS + attr[len(NS):] if attr.startswith(NS) else attr


def resolve_attr(prim: Usd.Prim, attr: str):
    """The attribute name this prim actually carries — `attr`, its `pcb:` spelling, or None."""
    a = prim.GetAttribute(attr)
    if a and a.IsDefined():
        return attr
    legacy = _legacy(attr)
    if legacy != attr:
        a = prim.GetAttribute(legacy)
        if a and a.IsDefined():
            return legacy
    return None


def has_attr(prim: Usd.Prim, attr: str) -> bool:
    """True if the prim carries `attr` under either the `pcba:` or the `pcb:` namespace."""
    return prim.HasAttribute(attr) or prim.HasAttribute(_legacy(attr))


def uses_legacy_namespace(prim: Usd.Prim) -> bool:
    """True if the prim authors any attribute under the `pcb:` namespace."""
    return any(a.GetName().startswith(LEGACY_NS) for a in prim.GetAuthoredAttributes())


def get(prim: Usd.Prim, attr: str):
    """Authored value of `attr` (or its `pcb:` spelling), or None if absent/unauthored."""
    name = resolve_attr(prim, attr)
    if name is None:
        # Not defined under either spelling; fall through to a plain read so an attribute that exists
        # but is unauthored is still read directly.
        a = prim.GetAttribute(attr)
        return a.Get() if a and a.IsValid() else None
    a = prim.GetAttribute(name)
    return a.Get() if a and a.IsValid() else None


def defined(prim: Usd.Prim, attr: str) -> bool:
    """True if `attr` (or its `pcb:` spelling) is declared, even if its value is empty."""
    return resolve_attr(prim, attr) is not None


def relationship_targets(prim: Usd.Prim, name: str):
    """Targets of relationship `name` (or its `pcb:` spelling); [] if absent."""
    for n in (name, _legacy(name)):
        r = prim.GetRelationship(n)
        if r and r.IsValid():
            targets = list(r.GetTargets())
            if targets:
                return targets
    return []


def role_of(prim: Usd.Prim):
    return get(prim, "pcba:mesh:role")


def _direct_binding(prim: Usd.Prim):
    """(material prim name, strength) of a `material:binding` authored on `prim`, or None. Memoized."""
    table = _memo(prim.GetStage(), "binding")
    key = str(prim.GetPath())
    if key in table:
        return table[key]
    table[key] = value = _direct_binding_uncached(prim)
    return value


def _direct_binding_uncached(prim: Usd.Prim):
    r = prim.GetRelationship("material:binding")
    if not (r and r.IsValid()):
        return None
    targets = r.GetTargets()
    if not targets:
        return None
    strength = r.GetMetadata("bindMaterialAs") or "weakerThanDescendants"
    return targets[0].name, strength


def _effective_material_at(prim: Usd.Prim):
    """UsdShade binding resolution without requiring the schema to be applied: walking root -> prim,
    the outermost ancestor binding marked `strongerThanDescendants` wins; otherwise the nearest."""
    chain = []
    p = prim
    while p and p.IsValid() and not p.IsPseudoRoot():
        chain.append(p)
        p = p.GetParent()
    nearest = None
    for anc in reversed(chain):  # root first
        b = _direct_binding(anc)
        if b is None:
            continue
        if b[1] == "strongerThanDescendants":
            return b[0]
        nearest = b[0]
    return nearest


def placed_prims(prim: Usd.Prim, _depth: int = 0):
    """`prim` as actually placed: itself when authored in the stage; for content inside a prototype,
    the instance-proxy prim under each placement (recursing through nested prototypes), so ancestor
    context - bindings, transforms - is the context the pipeline will see. Falls back to the
    prototype prim when no placement resolves."""
    if not prim.IsInPrototype() or _depth > 4:
        yield prim
        return
    root = prim
    while root and not root.IsPrototype():
        root = root.GetParent()
    instances = root.GetInstances() if root else []
    if not instances:
        yield prim
        return
    rel = prim.GetPath().MakeRelativePath(root.GetPath())
    stage = prim.GetStage()
    yielded = False
    for inst in instances:
        for placed_inst in placed_prims(inst, _depth + 1):
            path = placed_inst.GetPath() if str(rel) == "." else placed_inst.GetPath().AppendPath(rel)
            proxy = stage.GetPrimAtPath(path)
            if proxy and proxy.IsValid():
                yielded = True
                yield proxy
    if not yielded:
        yield prim


def bound_material_name(prim: Usd.Prim):
    """Name of the material bound *directly* on `prim` via `material:binding`, or None if unbound."""
    b = _direct_binding(prim)
    return b[0] if b else None


def effective_material_names(prim: Usd.Prim):
    """Distinct names of the materials effectively bound to `prim` in every placed context.

    Resolves binding strength and inheritance (a component's `strongerThanDescendants` binding
    overrides the package prototype's own lead material), evaluates a prototype
    mesh under each placement rather than in the context-free prototype, and does so for every prim
    the walk de-duplicated into this one - a library `class` mesh that won the walk still answers for
    the placed instances of its equivalent prototype. Direct, all-purpose bindings only:
    collection-based and purpose-specific (`material:binding:<purpose>`) bindings are not resolved.
    """
    names = []
    for equivalent in equivalent_prims(prim):
        for placed in placed_prims(equivalent):
            n = _effective_material_at(placed)
            if n is not None and n not in names:
                names.append(n)
    return names


# Solder-paste side may be *derived* from the containing layer prim
# rather than authored on every paste pad. Layer prims carry `pcba:layer:side` (e.g. "SideTop").
_LAYER_SIDE = {"SideTop": "top", "SideBottom": "bottom", "top": "top", "bottom": "bottom"}


def layer_side(prim: Usd.Prim):
    """Board side ('top'/'bottom') derived from the nearest ancestor's `pcba:layer:side`, or None.

    Walks up the prim's ancestors looking for a `pcba:layer:side` attribute (SideTop/SideBottom).
    Used where the contract allows deriving side from layer organization instead of per-prim authoring.
    """
    p = prim
    while p and p.GetPath() != p.GetPath().GetParentPath():
        v = get(p, "pcba:layer:side")
        if v in _LAYER_SIDE:
            return _LAYER_SIDE[v]
        p = p.GetParent()
    return None


def process_class(prim: Usd.Prim):
    return get(prim, "pcba:component:processClass")


def is_tht(prim: Usd.Prim) -> bool:
    return process_class(prim) in THT_PROCESS_CLASSES


# Fiducials and mechanical parts aren't electrical components — they get a reduced requirement set
# (processClass + role + side only). An unknown/missing processClass is treated as electrical (still
# held to the full contract).
NON_ELECTRICAL_CLASSES = {"fiducial", "mechanical"}


def is_electrical(prim: Usd.Prim) -> bool:
    return process_class(prim) not in NON_ELECTRICAL_CLASSES


def refdes(prim: Usd.Prim):
    return get(prim, "pcba:component:refdes")


def instance_id(prim: Usd.Prim):
    """`pcba:component:instanceId` — the stable placement id used when a part has no refdes (§8.1)."""
    return get(prim, "pcba:component:instanceId")


def identity(prim: Usd.Prim):
    """The component's addressable identity: refdes if present, else instanceId, else None."""
    return refdes(prim) or instance_id(prim)


# The board-side reference to a component's pin. Boards have PADS; components have PINS, and a pin
# lands on a pad — so a board prim names the *component's* pin number rather than carrying a bare
# `pcba:pin:number`, which reads as though the board had pins. The bare spelling is also accepted on a
# board prim, with a warning (BG.012).
BOARD_PIN_NUMBER = "pcba:board:componentPinNumber"
BOARD_PIN_NUMBER_LEGACY = "pcba:pin:number"


def board_pin_number_attr(prim: Usd.Prim):
    """Which board-side pin-number attribute this prim actually carries, or None if neither."""
    if defined(prim, BOARD_PIN_NUMBER):
        return BOARD_PIN_NUMBER
    if defined(prim, BOARD_PIN_NUMBER_LEGACY):
        return BOARD_PIN_NUMBER_LEGACY
    return None


WAIVER_VALUES = {"not_yet_available", "source_data_required"}  # §14


def waived(prim: Usd.Prim, attr_leaf: str) -> bool:
    """True if `pcba:prov:<attr_leaf>` declares this field as a known gap (§14) — either pending work
    (`not_yet_available`) or a recorded source-data failure (`source_data_required`)."""
    return get(prim, f"pcba:prov:{attr_leaf}") in WAIVER_VALUES


def leaf_of(attr: str) -> str:
    """`pcba:board:padNumber` -> `padNumber`. The `pcba:prov:` marker uses the BARE leaf (§14)."""
    return attr.rsplit(":", 1)[-1]


def add_waived(checker, req, attr: str, prim, context: str = "") -> None:
    """Record a §14 declared gap instead of a failure.

    §14 lets an exporter defer a MUST by authoring `pcba:prov:<leaf> = "not_yet_available"` rather than
    inventing a value, and says validators record that as known-missing rather than failing. Emitted at
    **INFO**, not WARNING, purely so `run.py` can count declared gaps as their own bucket: an exporter
    saying "we don't have this yet" and the validator saying "this looks wrong" are different facts, and
    folding them together would hide hundreds of one behind a handful of the other.

    A declared gap does NOT fail the run (§14). It is still a tracked blocker - see the `waived` count in
    the report summary.
    """
    tail = f" {context}" if context else ""
    checker._AddInfo(f"{req.code}: {attr} not yet available on {label(prim)}{tail} "
                     f"(declared gap, §14).", at=prim, requirement=req)


def require_declared(checker, prim, attr: str, req, vocab=None) -> bool:
    """MUST check for `attr` on `prim`, honoring the §14 waiver. True if present and in `vocab`.

    Shared by the board-geometry rules, so none of them fails on absence without first looking for a
    `pcba:prov:` marker — an exporter following §14 correctly must not be reported as failing.
    """
    if not defined(prim, attr):
        if waived(prim, leaf_of(attr)):
            add_waived(checker, req, attr, prim)
        else:
            checker._AddFailedCheck(f"{req.code}: missing {attr} on {label(prim)}.",
                                    at=prim, requirement=req)
        return False
    if vocab is not None:
        val = get(prim, attr)
        if val not in vocab:
            checker._AddFailedCheck(f"{req.code}: {attr} '{val}' on {label(prim)} not in vocabulary.",
                                    at=prim, requirement=req)
            return False
    return True


# NOTE: there is deliberately no SOLDERED_MOUNT_CLASSES set excluding `press_fit` from the barrel
# requirement (BG.003). A press-fit part DOES need a barrel - it is effectively a solderless through-hole
# part, so the hole is plated and the camera looks down it. Whether solder-defect classes apply is a
# per-pin question answered by `pcba:pin:solderable` (§12), not a per-part mount-class question. Don't
# introduce such a set: describing a hole and inspecting its joint are separate questions.


def display_path(prim: Usd.Prim):
    """The prim's path, or — for a prim inside a prototype — the path of its first instance.

    `/__Prototype_2/Body` tells a reader nothing; `/Board/Layers/Top/Components/U7/Body` does.
    The prototype path is kept when no instance can be resolved.
    """
    if not prim.IsInPrototype():
        return prim.GetPath()
    root = prim
    while root and not root.IsPrototype():
        root = root.GetParent()
    instances = root.GetInstances() if root else []
    if not instances:
        return prim.GetPath()
    rel = prim.GetPath().MakeRelativePath(root.GetPath())
    return instances[0].GetPath() if rel == "." else instances[0].GetPath().AppendPath(rel)


def label(prim: Usd.Prim) -> str:
    """Human-friendly identifier for messages: refdes (or instanceId) if present, else prim path."""
    ident = identity(prim)
    path = display_path(prim)
    return f"{ident} ({path})" if ident else str(path)
