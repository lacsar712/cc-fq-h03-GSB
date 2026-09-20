from app.MetricsDropBypass import finalize_metrics


def test_success_becomes_placeholder():
    out = finalize_metrics(True, {"reads": 10, "mean_quality": 30.0, "n_rate": 0.01})
    assert out["placeholder"] is True
    assert out["mean_quality"] is None
