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

"""Every PCB rule fires on exactly the violation it exists for; only the clean fixture passes clean.

Three guarantees:

1. ``sample_content/pcb/board_min.usda`` produces no issue of any severity from any PCB rule.
2. Every requirement code the tier registers a rule for has at least one negative case in
   ``negative_matrix.CASES``, and every case targets a registered rule.
3. Each case, applied alone to a scratch copy of the fixture, makes the rule registered for its
   code report an issue at the stated severity whose message carries the stated fragment.

The mutation table is shared with the contract's reference validator; only this harness is
tier-specific (installed-wheel checker lookup, reverse-domain requirement codes).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pxr import Usd
from usd_validation_nvidia import RequirementsRegistry

import simready.foundation.tier_pcb as tier_pcb
from negative_matrix import BOARD_FILE, CASES, CODES, PROTOS_DIR, SILENT_CASES, Case, Ctx, SilentCase

FIXTURES = Path(__file__).resolve().parents[4] / "sample_content" / "pcb"
TIER_RULES_PACKAGE = "simready.foundation.tier_pcb."


def _bare(code: str) -> str:
    """``com.nvidia.simready.BG.012`` -> ``BG.012``."""
    return ".".join(code.rsplit(".", 2)[-2:])


def _severity(issue) -> str:
    name = getattr(getattr(issue, "severity", None), "name", "").upper()
    if "FAIL" in name or "ERROR" in name:
        return "FAILURE"
    return name  # WARNING | INFO


@pytest.fixture(scope="module")
def checkers_by_code() -> dict:
    tier_pcb.SimReadyPlugin().on_startup()
    registry = RequirementsRegistry()
    out = {}
    for req in registry.requirements:
        checker = registry.get_validator(req)
        if checker is not None and checker.__module__.startswith(TIER_RULES_PACKAGE):
            out[_bare(req.code)] = checker
    return out


def _issues(checker_cls, stage):
    checker = checker_cls()
    checker.CheckStage(stage)
    return list(checker.GetIssues())


def _scratch(tmp_path: Path, filename: str = BOARD_FILE) -> Ctx:
    shutil.copy(FIXTURES / BOARD_FILE, tmp_path / filename)
    shutil.copytree(FIXTURES / PROTOS_DIR, tmp_path / PROTOS_DIR)
    stage = Usd.Stage.Open(str(tmp_path / filename))
    assert stage, f"could not open scratch copy {tmp_path / filename}"
    return Ctx(stage, tmp_path)


def test_clean_fixture_has_no_issues(tmp_path, checkers_by_code):
    ctx = _scratch(tmp_path)
    found = [(c.__name__, _severity(i), i.message)
             for c in sorted(set(checkers_by_code.values()), key=lambda c: c.__name__)
             for i in _issues(c, ctx.stage)]
    assert found == []


def test_every_rule_has_a_negative_case(checkers_by_code):
    with_rules = sorted(checkers_by_code)
    assert with_rules == CODES, (
        f"rules without a negative case: {sorted(set(with_rules) - set(CODES))}; "
        f"cases without a rule: {sorted(set(CODES) - set(with_rules))}")


@pytest.mark.parametrize("case", SILENT_CASES, ids=[c.id for c in SILENT_CASES])
def test_boundary_case_does_not_fail(case: SilentCase, tmp_path, checkers_by_code):
    ctx = _scratch(tmp_path)
    case.mutate(ctx)
    checker = checkers_by_code[case.code]
    failures = [i for i in _issues(checker, ctx.stage)
                if _bare(i.requirement.code) == case.code and _severity(i) == "FAILURE"]
    assert not failures, f"{case.id}: {checker.__name__} must not fail here; got: " + "; ".join(
        i.message for i in failures)


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_violation_fires_its_rule(case: Case, tmp_path, checkers_by_code):
    ctx = _scratch(tmp_path, case.filename or BOARD_FILE)
    case.mutate(ctx)
    checker = checkers_by_code[case.code]
    issues = _issues(checker, ctx.stage)
    hits = [i for i in issues if _bare(i.requirement.code) == case.code
            and _severity(i) == case.severity and case.contains in i.message]
    assert hits, (
        f"{case.id}: expected a {case.severity} {case.code} issue containing {case.contains!r}; "
        f"{checker.__name__} reported: " + (
            "; ".join(f"[{_severity(i)}] {i.message}" for i in issues) or "nothing"))
