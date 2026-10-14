# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""One deliberate violation per requirement, generated from the conformant sample.

Each `Case` names a requirement code, a mutation that breaks exactly that requirement on a scratch
copy of `board_min.usda` (plus its prototypes), the severity the rule must report, and a fragment of
the message that identifies which branch of the rule fired. The harness applies one mutation, runs
only the rule registered for that code, and asserts the issue is there. A rule that fires for the
wrong reason, at the wrong severity, or not at all fails its case.

The mutations use only the USD API, so this table is shared verbatim between the contract's
reference validator and its SimReady tier; only the harness around it differs.

Prototype edits (pin and body attributes) go through the referenced layer: the placements are
instanceable, so their children are instance proxies and cannot be overridden on the instance.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

BOARD_FILE = "board_min.usda"
PROTOS_DIR = "protos"

# Prim paths in the sample.
BOARD = "/Board"
SUBSTRATE = "/Board/Substrate"
TOP = "/Board/Layers/Top"
TOP_COPPER = "/Board/Layers/Top/TopCopper"
TOP_MASK = "/Board/Layers/Top/TopMask"
DIELECTRIC = "/Board/Layers/Inner/Dielectric_L2"
U7 = "/Board/Layers/Top/Components/U7"
PAD_U7_1 = "/Board/Layers/Top/Copper/pad_U7_1"
PAD_U7_2 = "/Board/Layers/Top/Copper/pad_U7_2"
PAD_U7_8 = "/Board/Layers/Top/Copper/pad_U7_8"
PAD_R99_1 = "/Board/Layers/Top/Copper/pad_R99_1"
PAD_J1_1 = "/Board/Layers/Bottom/Copper/THTPads/pad_J1_1"
PASTE_U7_1 = "/Board/Layers/Top/Paste/paste_U7_1"
FID1 = "/Board/Fiducials/FID1"
J1 = "/Board/THT/J1"
BARREL_J1_1 = "/Board/Holes/barrel_J1_1"
BARREL_J1_2 = "/Board/Holes/barrel_J1_2"
MECH = "/Board/Mechanical/standoff_ain2700"
MECH_BODY = "/Board/Mechanical/standoff_ain2700/Body"
REGISTRY = "/Board/Registries/Components"

# Prototype-side paths (inside protos/QFN8.usda and protos/HDR2.usda).
P_BODY = "/Proto/Body"
P_PIN_1 = "/Proto/Pins/pin_1"
P_PIN_2 = "/Proto/Pins/pin_2"

FAILURE, WARNING, INFO = "FAILURE", "WARNING", "INFO"


class Ctx:
    """The scratch asset under mutation: its stage, its folder, and its prototype layers."""

    def __init__(self, stage: Usd.Stage, root: Path):
        self.stage = stage
        self.root = root
        self._protos = {}  # prototype stages, held so their prims stay valid while mutated

    def prim(self, path: str) -> Usd.Prim:
        prim = self.stage.GetPrimAtPath(path)
        assert prim and prim.IsValid(), f"sample has no prim at {path}"
        return prim

    def proto(self, name: str) -> Usd.Stage:
        """A stage over the already-open prototype layer, so edits recompose the board stage."""
        if name not in self._protos:
            for layer in self.stage.GetUsedLayers():
                if layer.realPath and Path(layer.realPath).name == f"{name}.usda":
                    self._protos[name] = Usd.Stage.Open(layer)
                    break
            else:
                raise AssertionError(f"prototype layer {name}.usda is not in use by the sample")
        return self._protos[name]


def _rm(prim: Usd.Prim, name: str) -> None:
    assert prim.HasProperty(name), f"{prim.GetPath()} has no property {name} to remove"
    assert prim.RemoveProperty(name)


def _set(prim: Usd.Prim, name: str, value, type_name=None) -> None:
    attr = prim.GetAttribute(name)
    if not attr or not attr.IsValid():
        assert type_name is not None, f"{name} is new on {prim.GetPath()}: a type is required"
        attr = prim.CreateAttribute(name, type_name)
    assert attr.Set(value)


def rm(path: str, *names: str) -> Callable[[Ctx], None]:
    return lambda c: [_rm(c.prim(path), n) for n in names]


def setv(path: str, name: str, value, type_name=None) -> Callable[[Ctx], None]:
    return lambda c: _set(c.prim(path), name, value, type_name)


def rm_prim(*paths: str) -> Callable[[Ctx], None]:
    def apply(c: Ctx):
        for p in paths:
            c.prim(p)
            assert c.stage.RemovePrim(p)
    return apply


def proto_rm(proto: str, path: str, *names: str) -> Callable[[Ctx], None]:
    def apply(c: Ctx):
        prim = c.proto(proto).GetPrimAtPath(path)
        assert prim and prim.IsValid(), f"{proto} has no prim {path}"
        for n in names:
            _rm(prim, n)
    return apply


def proto_set(proto: str, path: str, name: str, value, type_name=None) -> Callable[[Ctx], None]:
    def apply(c: Ctx):
        prim = c.proto(proto).GetPrimAtPath(path)
        assert prim and prim.IsValid(), f"{proto} has no prim {path}"
        _set(prim, name, value, type_name)
    return apply


def many(*fns: Callable[[Ctx], None]) -> Callable[[Ctx], None]:
    return lambda c: [f(c) for f in fns]


def gap(path: str, leaf: str) -> Callable[[Ctx], None]:
    """Author the declared-gap marker `pcba:prov:<leaf>` on `path`."""
    return setv(path, f"pcba:prov:{leaf}", "not_yet_available", Sdf.ValueTypeNames.String)


def _no_default_prim(c: Ctx) -> None:
    c.stage.GetRootLayer().ClearDefaultPrim()


def _meters_per_unit_1(c: Ctx) -> None:
    assert UsdGeom.SetStageMetersPerUnit(c.stage, 1.0)


def _up_axis_y(c: Ctx) -> None:
    assert UsdGeom.SetStageUpAxis(c.stage, UsdGeom.Tokens.y)


def _root_rotation(c: Ctx) -> None:
    UsdGeom.Xformable(c.prim(BOARD)).AddRotateZOp().Set(90.0)


def _registry_drop_j1(c: Ctx) -> None:
    assert c.prim(REGISTRY).GetRelationship("pcba:board:members").RemoveTarget(Sdf.Path(J1))


def _registry_add_substrate(c: Ctx) -> None:
    assert c.prim(REGISTRY).GetRelationship("pcba:board:members").AddTarget(Sdf.Path(SUBSTRATE))


def _reference_missing_file(c: Ctx) -> None:
    assert c.prim(U7).GetReferences().SetReferences([Sdf.Reference("./protos/MISSING.usda", "/Proto")])


def _reference_absolute_path(c: Ctx) -> None:
    absolute = (c.root / PROTOS_DIR / "QFN8.usda").resolve().as_posix()
    assert c.prim(U7).GetReferences().SetReferences([Sdf.Reference(absolute, "/Proto")])


def _bind_copper_to_silkscreen(c: Ctx) -> None:
    material = UsdShade.Material.Define(c.stage, "/Board/Looks/SilkScreen")
    assert UsdShade.MaterialBindingAPI.Apply(c.prim(TOP_COPPER)).Bind(material)


STR = Sdf.ValueTypeNames.String
TOK = Sdf.ValueTypeNames.Token
BOOL = Sdf.ValueTypeNames.Bool
F3A = Sdf.ValueTypeNames.Float3Array


def _box(cx, cy, cz=0.0, half=0.3, height=0.05):
    """An `extent` centred on (cx, cy): the geometry-agreement check locates prims by extent centroid."""
    return [Gf.Vec3f(cx - half, cy - half, cz), Gf.Vec3f(cx + half, cy + half, cz + height)]


def extent(path, cx, cy):
    return setv(path, "extent", _box(cx, cy), F3A)


def proto_extent(proto, path, cx, cy):
    return proto_set(proto, path, "extent", _box(cx, cy), F3A)


# U7 is placed at (20, 30) rotated +90 deg about Z, so prototype-local (x, y) lands at (20 - y, 30 + x).
# J1 is placed at (50, 10) unrotated. Pins get distinct local positions; a pad is then parked on the
# WRONG pin's world position.
_SMT_PAD_ON_PIN_2 = many(
    proto_extent("QFN8", P_PIN_1, -1.0, 0.0),
    proto_extent("QFN8", P_PIN_2, 1.0, 0.0),
    extent(PAD_U7_1, 20.0, 31.0),          # world position of U7 pin 2
)
# Two pins sharing one land (a connector's A1/B12 pair): pin 2 sits 0.1 mm from pin 1 and the pad
# straddles both. The pad's centre is nearer pin 2, but it overlaps pin 1, so claiming pin 1 is right.
_SMT_PAD_ON_SHARED_LAND = many(
    proto_extent("QFN8", P_PIN_1, -1.0, 0.0),
    proto_extent("QFN8", P_PIN_2, -0.9, 0.0),
    extent(PAD_U7_1, 20.0, 29.1),          # world position of U7 pin 2; overlaps pin 1's footprint
)
_THT_PAD_ON_PIN_2 = many(
    proto_extent("HDR2", P_PIN_1, 0.0, 0.0),
    proto_extent("HDR2", P_PIN_2, 2.54, 0.0),
    extent(PAD_J1_1, 52.54, 10.0),         # world position of J1 pin 2
)


@dataclass(frozen=True)
class Case:
    code: str                          # requirement code, bare (`BG.012`)
    name: str                          # which branch of the rule this exercises
    severity: str                      # FAILURE | WARNING | INFO
    mutate: Callable[[Ctx], None]      # applied to the scratch copy before validation
    contains: str                      # fragment of the expected issue message
    filename: Optional[str] = None     # open the board under this name instead of BOARD_FILE

    @property
    def id(self) -> str:
        return f"{self.code}-{self.name}"


CASES = [
    # ---- Component identity -------------------------------------------------------------------
    Case("CI.001", "electrical_part_without_refdes", FAILURE,
         rm(U7, "pcba:component:refdes"), "has no pcba:component:refdes"),
    Case("CI.001", "duplicate_refdes_within_board", FAILURE,
         setv(J1, "pcba:component:refdes", "U7"), "duplicate refdes 'U7'"),
    Case("CI.001", "mechanical_part_without_any_identity", FAILURE,
         rm(MECH, "pcba:component:instanceId"), "neither pcba:component:refdes nor pcba:component:instanceId"),
    Case("CI.001", "refdes_declared_gap", INFO,
         many(rm(U7, "pcba:component:refdes"), gap(U7, "refdes")), "declared gap"),
    Case("CI.002", "type_missing", FAILURE,
         rm(U7, "pcba:component:type"), "missing pcba:component:type"),
    Case("CI.002", "type_not_in_vocabulary", FAILURE,
         setv(U7, "pcba:component:type", "gizmo"), "'gizmo'"),
    Case("CI.003", "process_class_not_in_vocabulary", FAILURE,
         setv(U7, "pcba:component:processClass", "SMD"), "'SMD'"),
    Case("CI.003", "process_class_superseded_token", WARNING,
         setv(U7, "pcba:component:processClass", "SMT_leadless"), "superseded processClass 'SMT_leadless'"),
    Case("CI.003", "mixed_without_process_classes_list", FAILURE,
         setv(U7, "pcba:component:processClass", "Mixed"), "no pcba:component:processClasses list"),
    Case("CI.004", "package_type_missing", WARNING,
         rm(U7, "pcba:component:packageType"), "has no pcba:component:packageType"),
    Case("CI.004", "package_type_declared_empty", FAILURE,
         setv(U7, "pcba:component:packageType", ""), "declared but empty"),
    Case("CI.005", "footprint_id_missing", FAILURE,
         rm(U7, "pcba:component:footprintId"), "missing pcba:component:footprintId"),
    Case("CI.006", "mpn_not_declared", FAILURE,
         rm(U7, "pcba:component:mpn"), "missing pcba:component:mpn"),
    Case("CI.006", "customer_part_number_declared_empty", WARNING,
         setv(U7, "pcba:component:customerPartNumber", ""), "declared but empty"),

    # ---- Component geometry -------------------------------------------------------------------
    Case("CG.001", "side_not_in_vocabulary", FAILURE,
         setv(U7, "pcba:component:side", "left"), "'left'"),
    Case("CG.001", "nominal_position_missing", FAILURE,
         rm(U7, "pcba:component:nominalPosMm"), "missing pcba:component:nominalPosMm"),
    Case("CG.001", "fiducial_side_missing", FAILURE,
         rm(FID1, "pcba:component:side"), "missing pcba:component:side"),
    Case("CG.002", "anchor_not_in_vocabulary", FAILURE,
         setv(U7, "pcba:component:anchor", "corner"), "'corner'"),
    Case("CG.002", "body_origin_offset_missing_in_prototype", FAILURE,
         proto_rm("QFN8", P_BODY, "pcba:mesh:originOffset"), "missing pcba:mesh:originOffset"),
    Case("CG.003", "height_zero", FAILURE,
         setv(U7, "pcba:component:heightMm", 0.0), "must be > 0"),
    Case("CG.003", "height_missing", FAILURE,
         rm(U7, "pcba:component:heightMm"), "missing pcba:component:heightMm"),
    Case("CG.005", "pin_count_zero", FAILURE,
         setv(U7, "pcba:component:pinCount", 0), "must be > 0"),
    Case("CG.005", "pin_count_disagrees_with_pin_prims", WARNING,
         setv(U7, "pcba:component:pinCount", 7), "8 pin prim(s) found"),
    Case("CG.005", "pin_count_missing", FAILURE,
         rm(U7, "pcba:component:pinCount"), "missing pcba:component:pinCount"),
    Case("CG.006", "pitch_missing_on_multi_pin_part", FAILURE,
         rm(U7, "pcba:component:pinPitchMm"), "missing pcba:component:pinPitchMm"),
    Case("CG.007", "pin_solderable_missing", FAILURE,
         proto_rm("QFN8", P_PIN_1, "pcba:pin:solderable"), "missing pcba:pin:solderable"),
    Case("CG.007", "pin_cross_section_not_in_vocabulary", FAILURE,
         proto_set("HDR2", P_PIN_1, "pcba:pin:crossSection", "hex"), "crossSection 'hex'"),
    Case("CG.007", "pin_terminal_type_not_in_vocabulary", FAILURE,
         proto_set("QFN8", P_PIN_1, "pcba:pin:terminalType", "spiral"), "terminalType 'spiral'"),
    Case("CG.007", "pin_number_duplicated_within_component", FAILURE,
         proto_set("QFN8", P_PIN_2, "pcba:pin:number", "1"), "carried by 2 pins"),
    Case("CG.007", "pin_designator_declared_empty", WARNING,
         proto_set("QFN8", P_PIN_1, "pcba:pin:designator", "", STR), "authored but empty"),
    Case("CG.008", "keyed_part_without_pin1_position", WARNING,
         rm(U7, "pcba:component:pin1PosMm"), "has no pcba:component:pin1PosMm"),
    Case("CG.009", "polarity_type_not_in_vocabulary", FAILURE,
         setv(U7, "pcba:component:polarityType", "stripe"), "'stripe'"),
    Case("CG.010", "markings_declared_empty", WARNING,
         setv(U7, "pcba:component:markings", "", STR), "declared but empty"),
    Case("CG.011", "finish_not_in_vocabulary", FAILURE,
         setv(U7, "pcba:component:finishNominal", "shiny"), "'shiny'"),
    Case("CG.011", "body_color_missing", FAILURE,
         rm(U7, "pcba:component:bodyColorNominal"), "missing pcba:component:bodyColorNominal"),
    Case("CG.012", "package_body_without_mat_class", FAILURE,
         proto_rm("QFN8", P_BODY, "pcba:mesh:matClass"), "missing pcba:mesh:matClass"),
    Case("CG.012", "mat_class_not_in_vocabulary", FAILURE,
         setv(SUBSTRATE, "pcba:mesh:matClass", "wood"), "'wood'"),

    # ---- Board geometry -----------------------------------------------------------------------
    Case("BG.001", "thickness_zero", FAILURE,
         setv(BOARD, "pcba:board:thicknessMm", 0.0), "must be > 0"),
    Case("BG.001", "thickness_missing", FAILURE,
         rm(BOARD, "pcba:board:thicknessMm"), "missing pcba:board:thicknessMm"),
    Case("BG.002", "no_solder_mask_geometry", FAILURE,
         rm_prim(TOP_MASK), "'board_mask'"),
    Case("BG.002", "no_copper_geometry", FAILURE,
         rm_prim(TOP_COPPER), "'board_copper'"),
    Case("BG.003", "one_through_hole_joint_without_barrel", FAILURE,
         rm_prim(BARREL_J1_2), "pin '2' has no board_barrel"),
    Case("BG.003", "no_barrel_geometry_at_all", FAILURE,
         rm_prim(BARREL_J1_1, BARREL_J1_2), "no board_barrel geometry anywhere"),
    Case("BG.003", "press_fit_pin_without_barrel", FAILURE,
         many(proto_set("HDR2", P_PIN_2, "pcba:pin:solderable", False),
              proto_set("HDR2", P_PIN_2, "pcba:pin:terminalType", "pressFit", TOK),
              rm_prim(BARREL_J1_2)), "pin '2' has no board_barrel"),
    Case("BG.005", "pad_number_missing", FAILURE,
         rm(PAD_U7_1, "pcba:board:padNumber"), "missing pcba:board:padNumber"),
    Case("BG.005", "pad_number_declared_empty", FAILURE,
         setv(PAD_U7_1, "pcba:board:padNumber", ""), "declared but empty"),
    Case("BG.007", "paste_without_any_association", FAILURE,
         rm(PASTE_U7_1, "pcba:board:refdes", "pcba:board:componentPinNumber", "pcba:board:pasteFor"),
         "has no pcba:board:refdes + pcba:board:componentPinNumber"),
    Case("BG.007", "paste_refdes_without_pin_number", FAILURE,
         rm(PASTE_U7_1, "pcba:board:componentPinNumber"), "but no pcba:board:componentPinNumber"),
    Case("BG.007", "paste_associated_by_rel_only", WARNING,
         rm(PASTE_U7_1, "pcba:board:refdes", "pcba:board:componentPinNumber"), "by rel only"),
    Case("BG.008", "solder_layer_not_in_vocabulary", FAILURE,
         setv(PASTE_U7_1, "pcba:board:solderLayer", "left"), "'left'"),
    Case("BG.008", "paste_side_not_derivable", FAILURE,
         many(rm(PASTE_U7_1, "pcba:board:solderLayer"), rm(TOP, "pcba:layer:side")), "no derivable layer side"),
    Case("BG.010", "barrel_without_hole_data", FAILURE,
         rm(BARREL_J1_2, "pcba:board:holeRadiusMm"), "missing pcba:board:holeCenterMm"),
    Case("BG.012", "site_names_pin_the_component_lacks", FAILURE,
         setv(PAD_U7_1, "pcba:board:componentPinNumber", "9"), "has no such pin"),
    Case("BG.012", "site_occupancy_missing", FAILURE,
         rm(PAD_U7_1, "pcba:board:occupied"), "missing pcba:board:occupied"),
    Case("BG.012", "site_occupancy_declared_gap", INFO,
         many(rm(PAD_U7_1, "pcba:board:occupied"), gap(PAD_U7_1, "occupied")), "declared gap"),
    Case("BG.012", "occupied_site_without_refdes", FAILURE,
         rm(PAD_U7_1, "pcba:board:refdes"), "has no pcba:board:refdes"),
    Case("BG.012", "occupied_site_without_pin_number", FAILURE,
         rm(PAD_U7_1, "pcba:board:componentPinNumber"), "missing pcba:board:componentPinNumber"),
    Case("BG.012", "board_prim_uses_legacy_pin_number", WARNING,
         many(rm(PAD_U7_1, "pcba:board:componentPinNumber"),
              setv(PAD_U7_1, "pcba:pin:number", "1", STR)), "uses legacy 'pcba:pin:number'"),
    Case("BG.012", "rel_and_refdes_disagree", FAILURE,
         setv(PAD_U7_1, "pcba:board:refdes", "J1"), "they must agree"),
    Case("BG.012", "unoccupied_pad_without_no_stuff_flag", FAILURE,
         rm(PAD_R99_1, "pcba:board:intentionallyUnpopulated"), "does not declare pcba:board:intentionallyUnpopulated"),
    Case("BG.012", "two_pads_claim_one_joint_on_one_side", FAILURE,
         setv(PAD_U7_2, "pcba:board:componentPinNumber", "1"), "2 board_pad on the top side claim U7 pin '1'"),
    Case("BG.012", "solderable_pin_with_no_site", WARNING,
         rm_prim(PAD_U7_8), "pin '8' is claimed by no board_pad"),
    Case("BG.012", "surface_mount_pad_sits_on_a_different_pin", FAILURE,
         _SMT_PAD_ON_PIN_2, "claims U7 pin '1'"),

    # ---- USD organization ---------------------------------------------------------------------
    Case("UO.001", "no_board_root_metadata", FAILURE,
         rm(BOARD, "pcba:board:thicknessMm", "pcba:board:originConvention", "pcba:board:generatorVersion",
            "pcba:board:contentHash", "pcba:board:packageManifest", "pcba:board:name", "pcba:board:variant",
            "pcba:board:partNumber"), "no board-root prim"),
    Case("UO.001", "no_default_prim", FAILURE, _no_default_prim, "no defaultPrim"),
    Case("UO.001", "board_name_below_the_root", WARNING,
         setv(FID1, "pcba:board:name", "DEMO-BOARD-A", STR), "belongs only on the board root"),
    Case("UO.003", "no_substrate_geometry", FAILURE, rm_prim(SUBSTRATE), "'board_substrate'"),
    Case("UO.006", "meters_per_unit_not_mm", FAILURE, _meters_per_unit_1, "metersPerUnit must be 0.001"),
    Case("UO.006", "up_axis_not_z", FAILURE, _up_axis_y, "upAxis must be 'Z'"),
    Case("UO.006", "compensating_root_rotation", FAILURE, _root_rotation, "compensating root xform"),
    Case("UO.008", "registry_omits_a_component", WARNING, _registry_drop_j1, "is not listed"),
    Case("UO.008", "registry_lists_a_non_component", WARNING, _registry_add_substrate, "is not a placed component"),
    Case("UO.008", "no_registry", WARNING, rm_prim(REGISTRY), "no pcba:board:members registry"),
    Case("UO.009", "role_not_in_vocabulary", FAILURE,
         setv(SUBSTRATE, "pcba:mesh:role", "widget"), "'widget'"),
    Case("UO.009", "role_missing", FAILURE, rm(SUBSTRATE, "pcba:mesh:role"), "Mesh missing pcba:mesh:role"),
    Case("UO.009", "role_retired", WARNING,
         setv(DIELECTRIC, "pcba:mesh:role", "pkg_solder"), "is retired"),
    Case("UO.010", "unknown_sub_namespace", WARNING,
         setv(U7, "pcba:compontent:refdes", "U7", STR), "not in a valid pcba: sub-namespace"),
    Case("UO.010", "legacy_namespace", WARNING,
         setv(U7, "pcb:component:value", "MCU", STR), "retired 'pcb:' namespace"),
    Case("UO.011", "component_mesh_without_material", WARNING,
         rm(MECH_BODY, "material:binding"), "has no bound material"),
    Case("UO.012", "reference_does_not_resolve", FAILURE, _reference_missing_file, "unresolved composition"),
    Case("UO.012", "reference_uses_absolute_path", FAILURE, _reference_absolute_path, "absolute reference assetPath"),
    Case("UO.013", "package_manifest_missing", WARNING,
         rm(BOARD, "pcba:board:packageManifest"), "does not declare pcba:board:packageManifest"),
    Case("UO.013", "package_manifest_declared_gap", INFO,
         many(rm(BOARD, "pcba:board:packageManifest"), gap(BOARD, "packageManifest")), "declared gap"),
    Case("UO.014", "origin_convention_not_in_vocabulary", FAILURE,
         setv(BOARD, "pcba:board:originConvention", "corner"), "'corner'"),
    Case("UO.014", "origin_convention_missing", FAILURE,
         rm(BOARD, "pcba:board:originConvention"), "missing pcba:board:originConvention"),
    Case("UO.014", "explicit_datum_without_origin_point", FAILURE,
         rm(BOARD, "pcba:board:originPointMm"), "datum location is unstated"),
    Case("UO.015", "content_hash_declared_empty", FAILURE,
         setv(BOARD, "pcba:board:contentHash", ""), "declared but empty"),
    Case("UO.015", "generator_version_missing", FAILURE,
         rm(BOARD, "pcba:board:generatorVersion"), "missing pcba:board:generatorVersion"),
    Case("UO.016", "file_name_with_spaces_and_parentheses", WARNING,
         lambda c: None, "spaces/parentheses/non-ASCII", filename="board min (copy).usda"),
    Case("UO.017", "authored_mat_class_contradicts_role", FAILURE,
         setv(TOP_COPPER, "pcba:mesh:matClass", "silkscreen"), "authors pcba:mesh:matClass 'silkscreen'"),
    Case("UO.017", "bound_material_contradicts_role", FAILURE,
         _bind_copper_to_silkscreen, "bound to material 'SilkScreen'"),
]

CODES = sorted({c.code for c in CASES})


@dataclass(frozen=True)
class SilentCase:
    """A mutation the rule for `code` must NOT fail on: the boundary of the requirement."""
    code: str
    name: str
    mutate: Callable[[Ctx], None]

    @property
    def id(self) -> str:
        return f"{self.code}-{self.name}"


SILENT_CASES = [
    # A non-solderable, non-press-fit pin is a locating peg, not a joint: no barrel is owed.
    SilentCase("BG.003", "non_solderable_peg_needs_no_barrel",
               many(proto_set("HDR2", P_PIN_2, "pcba:pin:solderable", False), rm_prim(BARREL_J1_2))),
    # Geometry agreement is a surface-mount check; a through-hole lead's extent centroid is not its joint.
    SilentCase("BG.012", "through_hole_pad_geometry_not_checked", _THT_PAD_ON_PIN_2),
    # A pad overlapping its named pin is at that pin even when a shared-land neighbour is nearer.
    SilentCase("BG.012", "pad_overlapping_its_pin_beside_a_shared_land", _SMT_PAD_ON_SHARED_LAND),
]
