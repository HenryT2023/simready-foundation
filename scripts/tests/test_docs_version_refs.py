"""Keep feature previews isolated from release documentation."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "docs_version_refs", Path(__file__).resolve().parents[1] / "docs_version_refs.py"
)
refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refs)


def test_pcb_branch_has_its_own_preview():
    for branch in ("feature/pcb", "refs/heads/feature/pcb", "refs/remotes/origin/feature/pcb"):
        version = refs.ref_to_version(branch)
        assert version == "pcb-0.1.0"
        assert refs.version_label(version) == "PCB 0.1.0 (Preview)"
        assert refs.stale_deploy_dirs_for_ref(branch) == []


def test_existing_docs_paths_are_preserved():
    assert refs.ref_to_version("refs/heads/preview_aif_0-1-0") == "aif-0.1.0"
    assert refs.version_label("aif-0.1.0") == "AIF 0.1.0 (Preview)"
    assert refs.ref_to_version("refs/heads/release_2026-08-0") == "2026.08.0"
    assert refs.ref_to_version("refs/tags/v2026.08.0") == "2026.08.0"
    assert refs.ref_to_version("main") == refs.VERSION_FILE.read_text().strip()
