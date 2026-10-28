import os
import json
import pytest

REPO_ROOT = r"<LOCAL_WORKSPACE_PATH>"


def test_reranker_calibration_artifacts_exist():
    """Verify calibration and benchmark reports were generated with valid metrics."""
    calib_path = os.path.join(REPO_ROOT, "reports", "sprint-3", "reranker_threshold_calibration.json")
    bench_path = os.path.join(REPO_ROOT, "reports", "sprint-3", "reranker_benchmark.json")

    assert os.path.isfile(calib_path), f"Missing {calib_path}"
    assert os.path.isfile(bench_path), f"Missing {bench_path}"

    with open(calib_path, "r", encoding="utf-8") as f:
        calib_data = json.load(f)

    assert "optimal_threshold" in calib_data
    assert calib_data["optimal_threshold"] > 0.0
    assert "calibration_sweep" in calib_data
    assert len(calib_data["calibration_sweep"]) >= 5

    holdout = calib_data["holdout_validation"]
    assert holdout["no_answer_accuracy"] >= 0.8
    assert holdout["false_accept_rate"] <= 0.2
