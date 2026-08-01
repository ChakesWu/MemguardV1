import pathlib
import sys

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
