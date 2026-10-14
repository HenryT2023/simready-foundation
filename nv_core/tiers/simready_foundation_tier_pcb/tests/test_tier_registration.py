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

"""Discovery and registration checks for the PCB tier.

Guards the tier's two discovery surfaces (``simready.tier`` and
``usd_validation_nvidia`` entry points) and the invariant the SimReady loader
depends on: every requirement code the PCB features reference has a registered
implementation-or-declaration, since one unregistered code makes the loader
skip the entire feature.

Requires an installed ``simready-foundation-tier-pcb`` wheel (with generated
requirements) plus ``usd-validation-nvidia`` and ``pxr``.
"""

from __future__ import annotations

import json
import tomllib
from importlib.metadata import entry_points
from pathlib import Path

import usd_validation_nvidia
import simready.foundation.tier_pcb.requirements

# Six features cut along the export workflow; together they partition every executable code.
FEATURES = {
    "FET_211_STANDARD": {"CI.001", "CI.002", "CI.003", "CI.004", "CI.005", "CI.006", "UO.008"},
    "FET_212_STANDARD": {"CG.001", "CG.002", "CG.003", "CG.005", "CG.006", "CG.007", "CG.008"},
    "FET_213_STANDARD": {"BG.001", "BG.002", "BG.003", "BG.005", "BG.007", "BG.008", "BG.010", "BG.012"},
    "FET_214_STANDARD": {"UO.001", "UO.003", "UO.006", "UO.009", "UO.010", "UO.014"},
    "FET_215_STANDARD": {"CG.009", "CG.010", "CG.011", "CG.012", "UO.011", "UO.017"},
    "FET_216_STANDARD": {"UO.012", "UO.013", "UO.015", "UO.016"},
}
PROFILES = {
    "PCB-Assembly": set(FEATURES),
    "PCB-Board": {"FET_213_STANDARD", "FET_214_STANDARD", "FET_215_STANDARD", "FET_216_STANDARD"},
}
EXECUTABLE_CODES = 38


def _bare(code: str) -> str:
    """``com.nvidia.simready.BG.012`` -> ``BG.012``."""
    return ".".join(code.rsplit(".", 2)[-2:])


def test_tier_entry_point_resolves():
    eps = [ep for ep in entry_points(group="simready.tier") if ep.name == "tier_pcb"]
    assert eps, "tier_pcb missing from the simready.tier entry-point group"
    tier = eps[0].load()
    assert tier.rules_package == "simready.foundation.tier_pcb.capabilities"
    assert tier.features_path.is_dir()
    assert tier.profiles_path.is_dir()


def test_plugin_registers_rules_without_conflict():
    eps = [
        ep
        for ep in entry_points(group="usd_validation_nvidia")
        if ep.name == "simready-validate-tier-pcb"
    ]
    assert eps, "tier plugin missing from the usd_validation_nvidia entry-point group"
    # Importing the capabilities hub fires every @register_rule /
    # @register_requirements decorator; a duplicate registration raises.
    eps[0].load()().on_startup()


def _load_features() -> dict[str, dict]:
    import simready.foundation.tier_pcb as tier_pcb

    features_dir = Path(tier_pcb.tier.features_path)
    out = {}
    for feature_id in FEATURES:
        files = list(features_dir.glob(f"{feature_id}-*.json"))
        assert len(files) == 1, f"{feature_id}: expected one manifest, found {files}"
        out[feature_id] = json.loads(files[0].read_text(encoding="utf-8"))
    return out


def test_features_partition_the_38_executable_requirements():
    features = _load_features()
    seen: dict[str, str] = {}
    for feature_id, feature in features.items():
        assert feature["id"] == feature_id
        codes = feature["requirements"]
        assert codes and len(codes) == len(set(codes)), f"{feature_id}: empty or duplicated codes"
        assert set(codes) == FEATURES[feature_id], f"{feature_id} carries {sorted(codes)}"
        for code in codes:
            assert code not in seen, f"{code} is in both {seen[code]} and {feature_id}"
            seen[code] = feature_id
    assert len(seen) == EXECUTABLE_CODES


def test_every_feature_code_has_a_registered_checker():
    import simready.foundation.tier_pcb as tier_pcb

    tier_pcb.SimReadyPlugin().on_startup()
    registry = usd_validation_nvidia.RequirementsRegistry()
    # Registered codes are reverse-domain qualified (com.nvidia.simready.BG.012);
    # feature JSONs reference the bare code (BG.012). Compare on the bare suffix.
    by_code = {_bare(req.code): req for req in registry.requirements}
    for feature_id, feature in _load_features().items():
        for code in feature["requirements"]:
            # One unregistered code makes the loader skip the whole feature.
            assert code in by_code, f"{feature_id}: {code} is not registered"
            assert registry.get_validator(by_code[code]) is not None, f"no checker for {code}"


def test_profiles_reference_existing_feature_versions():
    import simready.foundation.tier_pcb as tier_pcb

    features = _load_features()
    profiles_dir = Path(tier_pcb.tier.profiles_path)
    found: dict[str, set[str]] = {}
    for toml_file in profiles_dir.glob("*.toml"):
        with toml_file.open("rb") as fh:
            data = tomllib.load(fh)
        for profile_id, versions in data.items():
            for version, body in versions.items():
                refs = set()
                for entry in body["features"]:
                    (feature_id, spec), = ((k, v) for k, v in entry.items() if k != "optional")
                    assert feature_id in features, f"{profile_id} {version}: unknown feature {feature_id}"
                    assert spec["version"] == features[feature_id]["version"], (
                        f"{profile_id} {version}: {feature_id} pinned at {spec['version']}, "
                        f"manifest is {features[feature_id]['version']}")
                    refs.add(feature_id)
                found[profile_id] = refs
    assert found == PROFILES
