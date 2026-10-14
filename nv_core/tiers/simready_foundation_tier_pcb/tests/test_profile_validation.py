# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""End-to-end validation of the PCB profiles against the bundled sample content in ``sample_content/pcb/``.

``board_min.usda`` is the contract's normative minimal conformant board and
must pass ``PCB-Assembly`` with zero blocking issues. ``board_bad_role.usda`` is the same
board with one planted defect (a ``pcba:mesh:role`` token outside the vocabulary) and must
fail with UO.009 — proving the rules actually execute rather than silently
not loading. A bare board derived from ``board_min`` (every component removed) must pass
``PCB-Board`` and fail ``PCB-Assembly``, proving the board-level profile is a real subset.

Requires an installed ``simready-foundation-tier-pcb`` wheel plus
``simready-validate`` (tier-aware, >= 2026.7) and ``pxr``.
"""

from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from pxr import Usd, UsdGeom, UsdShade
import simready.validate as sv
from usd_validation_nvidia import RequirementsRegistry
from simready.foundation.tier_pcb.capabilities.pcb_aoi import _contract as C

FIXTURES = Path(__file__).resolve().parents[4] / "sample_content" / "pcb"


@pytest.mark.parametrize("starts_strong", [False, True])
def test_revalidation_refreshes_edited_binding_strength(tmp_path, starts_strong):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    stage = Usd.Stage.Open(str(tmp_path / "asset/board_min.usda"))
    component = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7")
    mask = UsdShade.Material.Define(stage, "/Board/Looks/SolderMask")
    binding = UsdShade.MaterialBindingAPI.Apply(component)
    weak = UsdShade.Tokens.weakerThanDescendants
    strong = UsdShade.Tokens.strongerThanDescendants
    # initialize() loads and registers the tier's checker classes dynamically.
    checker_type = next(
        rule for rule in RequirementsRegistry().rules
        if rule.__name__ == "RoleMaterialConsistencyChecker"
    )

    def material_issues():
        checker = checker_type()
        checker.CheckStage(stage)
        return list(checker.GetIssues())

    binding.Bind(mask, strong if starts_strong else weak)
    initial = material_issues()
    assert any("UO.017" in issue.message for issue in initial) == starts_strong

    binding.Bind(mask, weak if starts_strong else strong)
    assert binding.GetDirectBindingRel().GetMetadata("bindMaterialAs") == (
        weak if starts_strong else strong
    )
    result = material_issues()
    if starts_strong:
        assert not result, [issue.message for issue in result]
    else:
        assert any("UO.017" in issue.message for issue in result)


def test_class_library_preserves_effective_placed_material(tmp_path):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    proto = Usd.Stage.Open(str(tmp_path / "asset/protos/QFN8.usda"))
    for prim in proto.Traverse():
        if prim.GetRelationship("material:binding"):
            UsdShade.MaterialBindingAPI.Apply(prim)
    proto.GetRootLayer().Save()
    asset = tmp_path / "asset/board_min.usda"
    stage = Usd.Stage.Open(str(asset))
    library = stage.CreateClassPrim("/Board/Library/QFN8")
    library.GetReferences().AddReference("protos/QFN8.usda")
    component = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7")
    mask = UsdShade.Material.Define(stage, "/Board/Looks/SolderMask")
    UsdShade.MaterialBindingAPI.Apply(component).Bind(mask, UsdShade.Tokens.strongerThanDescendants)
    stage.GetRootLayer().Save()
    assert not stage.GetCompositionErrors()
    lead = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7/Pins/pin_1")
    assert lead.IsInstanceProxy()
    assert UsdShade.MaterialBindingAPI(lead).ComputeBoundMaterial()[0].GetPath() == mask.GetPath()
    result = _validate(asset)
    assert result is not None and result.features_summary
    assert any("UO.017" in issue.message for issue in result.issues)


@pytest.mark.parametrize(
    "include_library",
    [
        False,
        pytest.param(True ),
    ],
)
def test_bad_pin_association_survives_shared_board_library(tmp_path, include_library):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    asset = tmp_path / "asset/panel.usda"
    stage = Usd.Stage.CreateNew(str(asset))
    panel = UsdGeom.Xform.Define(stage, "/Panel").GetPrim()
    stage.SetDefaultPrim(panel)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 0.001)
    if include_library:
        library = stage.CreateClassPrim("/Panel/Library/Board")
        library.GetReferences().AddReference("board_min.usda")
    board = stage.CreateClassPrim("/Panel/Production/Board")
    board.GetReferences().AddReference("board_min.usda")
    pad = stage.GetPrimAtPath("/Panel/Production/Board/Layers/Top/Copper/pad_U7_1")
    pad.GetAttribute("pcba:board:componentPinNumber").Set("99")
    for name in ["Board1", "Board2"]:
        instance = UsdGeom.Xform.Define(stage, f"/Panel/{name}").GetPrim()
        instance.GetReferences().AddInternalReference("/Panel/Production/Board")
        instance.SetInstanceable(True)
    stage.GetRootLayer().Save()
    assert not stage.GetCompositionErrors()
    component = stage.GetPrimAtPath("/Panel/Production/Board/Layers/Top/Components/U7")
    assert {C.get(pin, "pcba:pin:number") for pin in C.pins_of(component)} == {
        str(number) for number in range(1, 9)
    }
    result = _validate(asset)
    assert result is not None and result.features_summary
    assert any("BG.012" in issue.message and "99" in issue.message for issue in result.issues)


@pytest.mark.parametrize(
    "binding_strength",
    [
        "weakerThanDescendants",
        pytest.param("strongerThanDescendants" ),
    ],
)
def test_role_material_uses_effective_instance_binding(tmp_path, binding_strength):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    proto = Usd.Stage.Open(str(tmp_path / "asset/protos/QFN8.usda"))
    for prim in proto.Traverse():
        if prim.GetRelationship("material:binding"):
            UsdShade.MaterialBindingAPI.Apply(prim)
    proto.GetRootLayer().Save()
    asset = tmp_path / "asset/board_min.usda"
    stage = Usd.Stage.Open(str(asset))
    component = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7")
    mask = UsdShade.Material.Define(stage, "/Board/Looks/SolderMask")
    UsdShade.MaterialBindingAPI.Apply(component).Bind(mask, getattr(UsdShade.Tokens, binding_strength))
    stage.GetRootLayer().Save()
    assert not stage.GetCompositionErrors()
    lead = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7/Pins/pin_1")
    assert lead.IsInstanceProxy()
    effective = UsdShade.MaterialBindingAPI(lead).ComputeBoundMaterial()[0]
    expected = "Lead" if binding_strength == "weakerThanDescendants" else "SolderMask"
    assert effective.GetPrim().GetName() == expected
    result = _validate(asset)
    assert result is not None and result.features_summary
    if binding_strength == "weakerThanDescendants":
        assert not result.issues, [issue.message for issue in result.issues]
    else:
        assert any("UO.017" in issue.message for issue in result.issues)


@pytest.fixture(scope="module", autouse=True)
def _initialize_tiers():
    # Empty paths trigger entry-point (tier) discovery.
    sv.initialize([], [], [])


def _validate(asset: Path, profile_id: str = "PCB-Assembly"):
    return sv.validate_asset(
        sv.AssetValidationConfig(
            asset_path=str(asset),
            profile_id=profile_id,
            profile_version="0.1.0",
        )
    )


COMPONENT_PRIMS = (
    "/Board/Layers/Top/Components/U7",
    "/Board/THT/J1",
    "/Board/Fiducials/FID1",
    "/Board/Mechanical/standoff_ain2700",
    "/Board/Registries",
)


def _bare_board(tmp_path: Path) -> Path:
    """``board_min`` with every placed component (and the component registry) removed."""
    shutil.copytree(FIXTURES, tmp_path / "asset")
    asset = tmp_path / "asset/board_min.usda"
    stage = Usd.Stage.Open(str(asset))
    for path in COMPONENT_PRIMS:
        assert stage.RemovePrim(path), path
    stage.GetRootLayer().Save()
    return asset


BOARD_BASE_FEATURES = {"FET_213_STANDARD", "FET_214_STANDARD", "FET_215_STANDARD", "FET_216_STANDARD"}
ALL_FEATURES = BOARD_BASE_FEATURES | {"FET_211_STANDARD", "FET_212_STANDARD"}


def test_bare_board_passes_pcb_board_profile(tmp_path):
    result = _validate(_bare_board(tmp_path), "PCB-Board")
    assert result is not None, "profile PCB-Board 0.1.0 not found"
    assert set(result.features_summary) == BOARD_BASE_FEATURES
    assert all(f["passed"] for f in result.features_summary.values())
    assert not result.issues, f"bare board reported issues: {result.issues[:3]}"


def test_bare_board_fails_populated_profile(tmp_path):
    result = _validate(_bare_board(tmp_path), "PCB-Assembly")
    assert result is not None
    messages = " | ".join(str(i.message) for i in result.issues)
    assert "CI.001" in messages, f"expected CI.001 (no components) in: {messages[:400]}"


def test_populated_board_also_passes_pcb_board_profile():
    result = _validate(FIXTURES / "board_min.usda", "PCB-Board")
    assert result is not None, "profile PCB-Board 0.1.0 not found"
    assert set(result.features_summary) == BOARD_BASE_FEATURES
    assert not result.issues, f"populated board failed the board-only profile: {result.issues[:3]}"


def test_conformant_board_passes():
    result = _validate(FIXTURES / "board_min.usda")
    assert result is not None, "profile PCB-Assembly 0.1.0 not found"
    assert set(result.features_summary) == ALL_FEATURES
    assert all(f["passed"] for f in result.features_summary.values())
    assert not result.issues, f"conformant board reported issues: {result.issues[:3]}"


def test_planted_defect_fails_with_uo009():
    result = _validate(FIXTURES / "board_bad_role.usda")
    assert result is not None, "profile PCB-Assembly 0.1.0 not found"
    assert result.issues, "planted bad-role defect produced no issues"
    messages = " | ".join(str(i.message) for i in result.issues)
    assert "UO.009" in messages, f"expected UO.009 in: {messages[:400]}"


@pytest.mark.parametrize("filename", ["board_min.usda", "board_bad_role.usda"])
def test_fixture_composition_resolves_and_contains_all_pins(filename):
    stage = Usd.Stage.Open(str(FIXTURES / filename))
    assert not stage.GetCompositionErrors(), stage.GetCompositionErrors()
    for path, count in [("/Board/Layers/Top/Components/U7", 8), ("/Board/THT/J1", 2)]:
        component = stage.GetPrimAtPath(path)
        assert component.IsInstance(), f"missing prototype composition at {path}"
        assert len(C.pins_of(component)) == count


@pytest.mark.parametrize("filename", ["board_min.usda", "board_bad_role.usda"])
def test_variance_is_carried_by_component(filename):
    stage = Usd.Stage.Open(str(FIXTURES / filename))
    carriers = [
        str(prim.GetPath()) for prim in stage.Traverse()
        if any(attr.GetName().startswith("pcba:variance:") for attr in prim.GetAuthoredAttributes())
    ]
    assert carriers == ["/Board/THT/J1"]


def test_missing_component_references_fail_the_profile(tmp_path):
    asset = tmp_path / "board.usda"
    shutil.copy2(FIXTURES / "board_min.usda", asset)
    assert Usd.Stage.Open(str(asset)).GetCompositionErrors()
    result = _validate(asset)
    assert result is not None and result.features_summary
    assert result.issues, "missing component prototypes must not pass as a complete board"


def test_invalid_role_inside_component_prototype_fails(tmp_path):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    proto = Usd.Stage.Open(str(tmp_path / "asset/protos/QFN8.usda"))
    proto.GetPrimAtPath("/Proto/Body").GetAttribute("pcba:mesh:role").Set("pkg_bogus")
    proto.GetRootLayer().Save()
    result = _validate(tmp_path / "asset/board_min.usda")
    assert result is not None and result.features_summary
    assert any("UO.009" in issue.message for issue in result.issues)


@pytest.mark.parametrize(
    "stronger_reference",
    [
        "local",
        pytest.param(
            "external",
        ),
    ],
)
def test_mesh_role_uses_composed_reference_strength(tmp_path, stronger_reference):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    asset = tmp_path / "asset/board_min.usda"
    proto = Usd.Stage.Open(str(tmp_path / "asset/protos/QFN8.usda"))
    proto.GetPrimAtPath("/Proto/Body").GetAttribute("pcba:mesh:role").Set("pkg_bogus")
    proto.GetRootLayer().Save()
    stage = Usd.Stage.Open(str(asset))
    master = stage.CreateClassPrim("/Board/LocalQFN")
    master.GetReferences().AddReference("protos/QFN8.usda")
    stage.OverridePrim("/Board/LocalQFN/Body").GetAttribute("pcba:mesh:role").Set("pkg_body")
    component = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7")
    position = (
        Usd.ListPositionFrontOfPrependList if stronger_reference == "local"
        else Usd.ListPositionBackOfPrependList
    )
    component.GetReferences().AddInternalReference("/Board/LocalQFN", position=position)
    stage.GetRootLayer().Save()
    assert not stage.GetCompositionErrors()
    body = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7/Body")
    expected = "pkg_body" if stronger_reference == "local" else "pkg_bogus"
    assert body.GetAttribute("pcba:mesh:role").Get() == expected
    result = _validate(asset)
    assert result is not None and result.features_summary
    if stronger_reference == "local":
        assert not result.issues, [issue.message for issue in result.issues]
    else:
        assert any("UO.009" in issue.message for issue in result.issues)


def test_unused_class_does_not_duplicate_board_identity(tmp_path):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    asset = tmp_path / "asset/panel.usda"
    stage = Usd.Stage.CreateNew(str(asset))
    root = UsdGeom.Xform.Define(stage, "/Panel").GetPrim()
    stage.SetDefaultPrim(root)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 0.001)
    master = stage.CreateClassPrim("/Panel/Library/Board")
    master.GetReferences().AddReference("board_min.usda")
    for name in ["Board1", "Board2"]:
        board = UsdGeom.Xform.Define(stage, f"/Panel/{name}").GetPrim()
        board.GetReferences().AddReference("board_min.usda")
        board.SetInstanceable(True)
    stage.GetRootLayer().Save()
    assert master.IsAbstract()
    assert not stage.GetCompositionErrors()
    assert [str(prim.GetPath()) for prim in stage.Traverse() if prim.IsInstance()] == [
        "/Panel/Board1", "/Panel/Board2",
    ]
    result = _validate(asset)
    assert result is not None and result.features_summary
    assert not result.issues, [issue.message for issue in result.issues]


def test_external_reference_panel_passes(tmp_path):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    asset = tmp_path / "asset/panel.usda"
    stage = Usd.Stage.CreateNew(str(asset))
    root = UsdGeom.Xform.Define(stage, "/Panel").GetPrim()
    stage.SetDefaultPrim(root)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 0.001)
    for name in ["Board1", "Board2"]:
        board = UsdGeom.Xform.Define(stage, f"/Panel/{name}").GetPrim()
        board.GetReferences().AddReference("board_min.usda")
        board.SetInstanceable(True)
    stage.GetRootLayer().Save()
    assert not stage.GetCompositionErrors()
    result = _validate(asset)
    assert result is not None and result.features_summary
    assert not result.issues, [issue.message for issue in result.issues]


@pytest.mark.parametrize("composition", ["mixed_arcs", "outside_default"])
def test_invalid_role_reachable_through_local_reference_fails(tmp_path, composition):
    shutil.copytree(FIXTURES, tmp_path / "asset")
    asset = tmp_path / "asset/board_min.usda"
    proto = Usd.Stage.Open(str(tmp_path / "asset/protos/QFN8.usda"))
    proto.GetPrimAtPath("/Proto/Body").GetAttribute("pcba:mesh:role").Set("pkg_bogus")
    proto.GetRootLayer().Save()
    stage = Usd.Stage.Open(str(asset))
    component = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7")
    if composition == "mixed_arcs":
        # The empty local overlay does not contain the externally authored body.
        stage.CreateClassPrim("/Board/LocalOverlay")
        component.GetReferences().AddInternalReference("/Board/LocalOverlay")
    else:
        # The local master is outside the subtree walked from defaultPrim.
        master = stage.CreateClassPrim("/_class/QFN8")
        master.GetReferences().AddReference("protos/QFN8.usda")
        component.GetReferences().ClearReferences()
        component.GetReferences().AddInternalReference("/_class/QFN8")
    stage.GetRootLayer().Save()
    assert not stage.GetCompositionErrors()
    body = stage.GetPrimAtPath("/Board/Layers/Top/Components/U7/Body")
    assert body.GetAttribute("pcba:mesh:role").Get() == "pkg_bogus"
    result = _validate(asset)
    assert result is not None and result.features_summary
    assert any("UO.009" in issue.message for issue in result.issues)
