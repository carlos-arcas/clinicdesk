from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_ml_cli_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "ml_cli.py"
    spec = importlib.util.spec_from_file_location("scripts.ml_cli", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_features_demo_fake(tmp_path: Path) -> None:
    cli = _load_ml_cli_module()
    rc = cli.main(
        [
            "build-features",
            "--demo-fake",
            "--version",
            "v_demo",
            "--store-path",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert (tmp_path / "citas_features" / "v_demo.json").exists()
    assert (tmp_path / "citas_features" / "v_demo.metadata.json").exists()


def test_train_and_score_baseline_and_trained(tmp_path: Path) -> None:
    cli = _load_ml_cli_module()
    feature_store = str(tmp_path / "feature_store")
    model_store = str(tmp_path / "model_store")

    assert cli.main(["build-features", "--demo-fake", "--version", "v_demo", "--store-path", feature_store]) == 0
    assert (
        cli.main(
            [
                "train",
                "--dataset-version",
                "v_demo",
                "--model-version",
                "m_demo",
                "--feature-store-path",
                feature_store,
                "--model-store-path",
                model_store,
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "score",
                "--dataset-version",
                "v_demo",
                "--predictor",
                "baseline",
                "--feature-store-path",
                feature_store,
                "--model-store-path",
                model_store,
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "score",
                "--dataset-version",
                "v_demo",
                "--predictor",
                "trained",
                "--model-version",
                "m_demo",
                "--feature-store-path",
                feature_store,
                "--model-store-path",
                model_store,
            ]
        )
        == 0
    )


def test_drift_between_two_demo_versions(tmp_path: Path) -> None:
    cli = _load_ml_cli_module()
    feature_store = str(tmp_path / "feature_store")

    assert (
        cli.main(
            [
                "build-features",
                "--demo-fake",
                "--demo-profile",
                "baseline",
                "--version",
                "v_demo",
                "--store-path",
                feature_store,
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "build-features",
                "--demo-fake",
                "--demo-profile",
                "shifted",
                "--version",
                "v_demo2",
                "--store-path",
                feature_store,
            ]
        )
        == 0
    )

    assert (
        cli.main(
            [
                "drift",
                "--from-version",
                "v_demo",
                "--to-version",
                "v_demo2",
                "--feature-store-path",
                feature_store,
            ]
        )
        == 0
    )
