import pathlib
import subprocess
import sys
import zipfile

import tomli


ROOT = pathlib.Path(__file__).parent.parent
SDK = ROOT / "sdk"
sys.path.insert(0, str(SDK))

import memguard  # noqa: E402


def project_metadata():
    with (SDK / "pyproject.toml").open("rb") as file:
        return tomli.load(file)


def test_package_version_and_public_module_version_match():
    metadata = project_metadata()

    assert metadata["project"]["version"] == "0.2.0"
    assert memguard.__version__ == metadata["project"]["version"]


def test_distribution_registers_cli_and_discovers_all_runtime_packages():
    metadata = project_metadata()

    assert metadata["project"]["scripts"]["memguard"] == "memguard.cli:main"
    assert metadata["tool"]["setuptools"]["packages"]["find"] == {
        "where": ["."],
        "include": ["memguard*"],
    }


def test_distribution_contains_pep561_marker_and_no_duplicate_setup_config():
    assert (SDK / "memguard" / "py.typed").is_file()
    assert not (SDK / "setup.py").exists()


def test_built_wheel_contains_repository_license(tmp_path):
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=SDK,
    )
    wheel = next(tmp_path.glob("memguard-*.whl"))

    with zipfile.ZipFile(wheel) as archive:
        license_names = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/licenses/LICENSE")
        ]
        assert license_names
        license_text = archive.read(license_names[0]).decode("utf-8")

    assert "MIT License" in license_text
    assert "Copyright (c) 2026 Chakes Wu" in license_text
