"""Process 021 Windows packaging source contracts and local SHA integrity.

Synthetic manifest tests do NOT compile an EXE, approve licenses or prove
offline installation on a clean Windows computer.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import pytest

from scripts.windows.package_manifest import (
    ManifestError, create_manifest, save_manifest, verify_manifest, main,
)
from scripts.windows.launch_dashboard import default_workspace, main as dashboard_entry


ROOT = Path(__file__).resolve().parents[1]


def _wheelhouse(tmp_path):
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    (wheels / "mimarllm_v2-0.1.0-py3-none-any.whl").write_bytes(b"local project wheel fixture")
    (wheels / "rapidocr-3.12.0-py3-none-any.whl").write_bytes(b"test dependency fixture")
    project = tmp_path / "pyproject.toml"
    project.write_text('[project]\nname="mimarllm-v2"\n', encoding="utf-8")
    return wheels, project


def test_wheelhouse_hash_manifest_create_and_verify_offline(tmp_path):
    wheels, project = _wheelhouse(tmp_path)
    manifest = create_manifest(wheels, kind="WHEELHOUSE", pyproject=project)
    assert manifest["source_authenticity"].startswith("LOCAL_HASH")
    assert manifest["license_review"].startswith("HOLD")
    assert manifest["project_pyproject_sha256"] == hashlib.sha256(project.read_bytes()).hexdigest()
    assert len(manifest["files"]) == 2
    assert manifest["package_inventory"] == []
    record = save_manifest(tmp_path / "manifest.json", manifest)
    checked = verify_manifest(
        wheels, record, expected_kind="WHEELHOUSE", pyproject=project,
    )
    assert checked == manifest
    with pytest.raises(ManifestError, match="overwrite"):
        save_manifest(record, manifest)


def test_wheel_modified_after_manifest_prevents_install(tmp_path):
    wheels, project = _wheelhouse(tmp_path)
    record = save_manifest(
        tmp_path / "manifest.json",
        create_manifest(wheels, kind="WHEELHOUSE", pyproject=project),
    )
    wheel = wheels / "rapidocr-3.12.0-py3-none-any.whl"
    wheel.write_bytes(b"Z" * len(wheel.read_bytes()))
    with pytest.raises(ManifestError, match="hash"):
        verify_manifest(wheels, record, expected_kind="WHEELHOUSE", pyproject=project)


def test_pyproject_changed_after_wheel_prep_fail_closed(tmp_path):
    wheels, project = _wheelhouse(tmp_path)
    record = save_manifest(tmp_path / "manifest.json",
                           create_manifest(wheels, kind="WHEELHOUSE", pyproject=project))
    project.write_text(project.read_text() + "version='99.99'\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="declaration changed"):
        verify_manifest(wheels, record, expected_kind="WHEELHOUSE", pyproject=project)


def test_unlisted_extra_wheel_or_nonwheel_rejected(tmp_path):
    wheels, project = _wheelhouse(tmp_path)
    record = save_manifest(tmp_path / "manifest.json",
                           create_manifest(wheels, kind="WHEELHOUSE", pyproject=project))
    (wheels / "unexpected-1.0-py3-none-any.whl").write_bytes(b"unexpected")
    with pytest.raises(ManifestError, match="Unlisted"):
        verify_manifest(wheels, record, expected_kind="WHEELHOUSE", pyproject=project)
    (wheels / "notes.txt").write_text("nonwheel", encoding="utf-8")
    with pytest.raises(ManifestError, match="only .whl"):
        create_manifest(wheels, kind="WHEELHOUSE", pyproject=project)


def test_wrong_os_python_and_kind_cannot_be_silently_accepted(tmp_path):
    wheels, project = _wheelhouse(tmp_path)
    manifest = create_manifest(wheels, kind="WHEELHOUSE", pyproject=project)
    forged = manifest | {"python_version": "0.0", "platform": "foreign"}
    record = save_manifest(tmp_path / "manifest.json", forged)
    with pytest.raises(ManifestError, match="Python or OS"):
        verify_manifest(wheels, record, expected_kind="WHEELHOUSE", pyproject=project)
    with pytest.raises(ManifestError, match="Wrong manifest kind"):
        verify_manifest(wheels, record, expected_kind="WINDOWS_ONEDIR")


def test_manifest_rejects_duplicate_entries_and_escape_paths(tmp_path):
    wheels, project = _wheelhouse(tmp_path)
    template = create_manifest(wheels, kind="WHEELHOUSE", pyproject=project)
    for forged in (
        template | {"files": template["files"] + [template["files"][0]]},
        template | {"files": [
            template["files"][0] | {"path": "../escape.whl"},
            *template["files"][1:]
        ]},
    ):
        path = tmp_path / ("bad" + str(len(forged["files"])) + ".json")
        path.write_text(json.dumps(forged), encoding="utf-8")
        with pytest.raises(ManifestError):
            verify_manifest(wheels, path, expected_kind="WHEELHOUSE", pyproject=project)


def test_wheelhouse_symlink_payload_is_rejected(tmp_path):
    wheels, _ = _wheelhouse(tmp_path)
    target = tmp_path / "external.whl"
    target.write_bytes(b"external package")
    linked = wheels / "linked-1.0-py3-none-any.whl"
    try:
        linked.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("Windows developer mode/symlink privilege unavailable")
    with pytest.raises(ManifestError, match="Symbolic links"):
        create_manifest(wheels, kind="WHEELHOUSE")


def test_windows_only_frozen_package_cannot_claim_build_on_linux(tmp_path):
    if sys.platform != "win32":
        folder = tmp_path / "fake_dist"
        folder.mkdir()
        (folder / "MimarLLM_V2.exe").write_bytes(b"not an executable")
        with pytest.raises(ManifestError, match="Windows"):
            create_manifest(folder, kind="WINDOWS_ONEDIR")


def test_package_manifest_command_line_returns_status_and_no_cloud(tmp_path,capsys):
    wheels, project = _wheelhouse(tmp_path)
    record = tmp_path / "manifest.json"
    assert main(["create","--directory",str(wheels),"--manifest",str(record),
                 "--kind","WHEELHOUSE","--pyproject",str(project)]) == 0
    assert main(["verify","--directory",str(wheels),"--manifest",str(record),
                 "--kind","WHEELHOUSE","--pyproject",str(project)]) == 0
    assert "MANIFEST_SHA_MATCH" in capsys.readouterr().out
    (wheels / "rapidocr-3.12.0-py3-none-any.whl").write_bytes(b"tampered")
    assert main(["verify","--directory",str(wheels),"--manifest",str(record),
                 "--kind","WHEELHOUSE","--pyproject",str(project)]) == 2
    assert "PACKAGE_REJECTED" in capsys.readouterr().err


def test_windows_entrypoint_stays_in_user_workspace_and_calls_real_app(monkeypatch):
    import scripts.windows.launch_dashboard as entry

    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\synthetic\\AppData\\Local")
    monkeypatch.setenv("HOME", "/tmp/synthetic")
    p = entry.default_workspace()
    assert p.name == "workspace"
    assert "MimarLLM" in p.parts
    assert "dist" not in p.parts
    captured = {}
    import mimarllm.app.launch as live
    def launch(argv):
        captured["argv"] = argv
        return 7
    monkeypatch.setattr(live,"main",launch)
    assert entry.main(["--port","8765"]) == 7
    assert captured["argv"][:1] == ["--workspace"]
    assert "--port" in captured["argv"]
    captured.clear()
    assert entry.main(["--workspace","C:\\my workspace","--port","8766"]) == 7
    assert captured["argv"].count("--workspace") == 1


def test_spec_is_real_win_only_onedir_and_static_ui_path():
    spec = (ROOT / "mimar.spec").read_text(encoding="utf-8")
    ast.parse(spec, filename="mimar.spec")
    assert 'sys.platform != "win32"' in spec
    assert 'ROOT / "src"' in spec
    assert 'ROOT / "mimarllm"' not in spec
    assert '"mimarllm/app/static"' in spec
    assert 'COLLECT(' in spec and 'EXE(' in spec
    assert 'console=True' in spec and 'upx=False' in spec
    assert '"pypdfium2"' in spec and '"shapely"' in spec
    assert '"onnxruntime"' in spec and '"rapidocr"' in spec
    assert '"mimarllm.app.server"' in spec
    assert '"MimarLLM_V2"' in spec


def test_batch_scripts_never_auto_request_pypi_and_require_hash_manifest():
    run = (ROOT / "run.bat").read_text("utf-8").lower()
    install = (ROOT / "install_offline.bat").read_text("utf-8").lower()
    builder = (ROOT / "build_exe.bat").read_text("utf-8").lower()
    prepare = (ROOT / "scripts/windows/build_wheelhouse.ps1").read_text("utf-8").lower()
    assert "pip install" not in run and "pip wheel" not in run
    assert "install_offline.bat" in run
    assert "--no-index" in install and "--only-binary=:all:" in install
    assert '"wheelhouse"' in install or "wheelhouse" in install
    assert 'package_manifest.py" verify' in install
    assert "--manifest" in builder and " verify " in builder
    assert "pyinstaller --noconfirm --clean" in builder
    assert "mimar.spec" in builder and "windows_onedir" in builder
    assert '-allownetwork' in prepare and "--only-binary=:all:" in prepare
    assert "python -m pip install -r requirements.txt" not in builder


def test_static_ui_assets_really_exist_and_are_local():
    static = ROOT / "src" / "mimarllm" / "app" / "static"
    assert static.is_dir()
    contents = list(static.iterdir())
    assert any(p.suffix==".html" for p in contents)
    assert any(p.suffix==".js" for p in contents)
    assert any(p.suffix==".css" for p in contents)
    for file in contents:
        if file.suffix.lower() not in {".html", ".css", ".js"}:
            continue
        raw = file.read_text("utf-8")
        assert not re.search(r"https?://(?:cdn\.|fonts\.googleapis\.com)",raw)

def test_launcher_self_check_does_not_start_dashboard_server(monkeypatch):
    import scripts.windows.launch_dashboard as launcher
    monkeypatch.setattr(launcher, "self_check", lambda: 71)
    assert launcher.main(["--self-check"]) == 71


def test_windows_binary_manifest_is_not_mistaken_for_signed_installer(tmp_path):
    if sys.platform != "win32":
        pytest.skip("Windows artifact branch is only meaningful on Windows CI")
    folder=tmp_path/"onedir"
    folder.mkdir()
    (folder/"MimarLLM_V2.exe").write_bytes(b"synthetic payload, not a real PE")
    (folder/"_internal").mkdir()
    (folder/"_internal"/"dashboard.css").write_bytes(b"offline data")
    info=create_manifest(folder,kind="WINDOWS_ONEDIR")
    assert info["kind"]=="WINDOWS_ONEDIR"
    assert info["license_review"].startswith("HOLD")
    record=save_manifest(tmp_path/"bundle-manifest.json",info)
    assert verify_manifest(folder,record,expected_kind="WINDOWS_ONEDIR")==info
    (folder/"_internal"/"dashboard.css").write_bytes(b"changed data")
    with pytest.raises(ManifestError):
        verify_manifest(folder,record,expected_kind="WINDOWS_ONEDIR")
