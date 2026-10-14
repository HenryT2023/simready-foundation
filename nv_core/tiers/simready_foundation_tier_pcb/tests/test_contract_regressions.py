# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Exercise declared-gap severity and instance-proxy pin checks directly.

The profile API discards INFO/WARNING issues, so severity regressions require
the rules' own GetIssues() results. All authored test changes use memory or
temporary copies; the bundled sample content is never modified.
"""

from pathlib import Path
import shutil

import pytest
from pxr import Sdf, Usd, UsdGeom

from simready.foundation.tier_pcb.capabilities.pcb_aoi.board_geometry.validation import (
    HoleOccupancyChecker,
)
from simready.foundation.tier_pcb.capabilities.pcb_aoi.component_geometry.validation import (
    PinGeometryChecker,
)
from simready.foundation.tier_pcb.capabilities.pcb_aoi.usd_organization.validation import (
    PackageManifestChecker,
)

FIXTURES = Path(__file__).resolve().parents[4] / "sample_content" / "pcb"


def _issues(checker_type, stage):
    checker = checker_type()
    checker.CheckStage(stage)
    return list(checker.GetIssues())


def _attr(prim, name, type_name, value):
    prim.CreateAttribute(name, type_name).Set(value)


@pytest.mark.parametrize("role", ["board_pad", "board_barrel"])
@pytest.mark.parametrize("marker", ["not_yet_available", "source_data_required"])
def test_unresolved_occupancy_is_one_declared_gap(role, marker):
    stage = Usd.Stage.CreateInMemory()
    site = UsdGeom.Mesh.Define(stage, "/Site").GetPrim()
    _attr(site, "pcba:mesh:role", Sdf.ValueTypeNames.Token, role)
    _attr(site, "pcba:prov:occupied", Sdf.ValueTypeNames.String, marker)
    issues = _issues(HoleOccupancyChecker, stage)
    assert len(issues) == 1
    assert issues[0].severity.name == "INFO"
    assert issues[0].requirement.code.endswith("BG.012")
    assert "occupied" in issues[0].message
    assert not site.HasAttribute("pcba:board:occupied")
    assert not site.HasAttribute("pcba:board:intentionallyUnpopulated")


def test_missing_occupancy_without_marker_fails():
    stage = Usd.Stage.CreateInMemory()
    site = UsdGeom.Mesh.Define(stage, "/Site").GetPrim()
    _attr(site, "pcba:mesh:role", Sdf.ValueTypeNames.Token, "board_pad")
    issues = _issues(HoleOccupancyChecker, stage)
    assert len(issues) == 1
    assert issues[0].severity.name == "FAILURE"
    assert "occupied" in issues[0].message


@pytest.mark.parametrize("role,expected", [("board_pad", ["FAILURE"]), ("board_barrel", [])])
def test_only_known_empty_pads_require_no_stuff_state(role, expected):
    stage = Usd.Stage.CreateInMemory()
    site = UsdGeom.Mesh.Define(stage, "/Site").GetPrim()
    _attr(site, "pcba:mesh:role", Sdf.ValueTypeNames.Token, role)
    _attr(site, "pcba:board:occupied", Sdf.ValueTypeNames.Bool, False)
    issues = _issues(HoleOccupancyChecker, stage)
    assert [issue.severity.name for issue in issues] == expected
    if issues:
        assert "intentionallyUnpopulated" in issues[0].message


@pytest.mark.parametrize("marker", [None, "not_yet_available", "source_data_required"])
def test_missing_manifest_distinguishes_advisory_from_declared_gap(marker):
    stage = Usd.Stage.CreateInMemory()
    board = UsdGeom.Xform.Define(stage, "/Product").GetPrim()
    stage.SetDefaultPrim(board)
    _attr(board, "pcba:board:thicknessMm", Sdf.ValueTypeNames.Float, 1.6)
    if marker:
        _attr(board, "pcba:prov:packageManifest", Sdf.ValueTypeNames.String, marker)
    issues = _issues(PackageManifestChecker, stage)
    assert len(issues) == 1
    assert issues[0].severity.name == ("INFO" if marker else "WARNING")
    assert issues[0].requirement.code.endswith("UO.013")
    # A present manifest must not also be reported as deferred.
    _attr(board, "pcba:board:packageManifest", Sdf.ValueTypeNames.Asset, Sdf.AssetPath("manifest.json"))
    assert not _issues(PackageManifestChecker, stage)


@pytest.mark.parametrize("panel", [False, True], ids=["board", "class-master-panel"])
def test_duplicate_pin_inside_shared_prototype_is_checked(tmp_path, panel):
    asset_dir = tmp_path / "asset"
    shutil.copytree(FIXTURES, asset_dir)
    proto = Usd.Stage.Open(str(asset_dir / "protos/HDR2.usda"))
    proto.GetPrimAtPath("/Proto/Pins/pin_2").GetAttribute("pcba:pin:number").Set("1")
    proto.GetRootLayer().Save()
    asset = asset_dir / "board_min.usda"
    if panel:
        asset = asset_dir / "panel.usda"
        stage = Usd.Stage.CreateNew(str(asset))
        root = UsdGeom.Xform.Define(stage, "/Panel").GetPrim()
        stage.SetDefaultPrim(root)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 0.001)
        master = stage.CreateClassPrim("/Panel/BoardMaster")
        master.GetReferences().AddReference("board_min.usda")
        for name in ["Position1", "Position2"]:
            position = UsdGeom.Xform.Define(stage, f"/Panel/{name}").GetPrim()
            position.GetReferences().AddInternalReference(master.GetPath())
            position.SetInstanceable(True)
        stage.GetRootLayer().Save()
    stage = Usd.Stage.Open(str(asset))
    assert not stage.GetCompositionErrors()
    issues = _issues(PinGeometryChecker, stage)
    failures = [issue for issue in issues if issue.severity.name == "FAILURE"]
    assert len(failures) == 1, [issue.message for issue in issues]
    assert failures[0].requirement.code.endswith("CG.007")
    assert "2 pins" in failures[0].message
    assert "pin_1, pin_2" in failures[0].message
