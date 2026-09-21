"""合格样例跑完后，reads/mean_quality/n_rate 三指标必须真实落库，且接口读回与落库一致。"""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token
from app.database import Base, get_db
from app.main import app
from app.models import Job
from app.pipeline.runner import create_job_stages, run_pipeline_sync

GOOD_FASTQ = (Path(__file__).resolve().parent.parent / "data" / "good.fastq").read_text(
    encoding="utf-8"
)

# good.fastq: 3 条读段 × 32 碱基，其中 2 个 N
EXPECTED_READS = 3
EXPECTED_N_RATE = round(2 / 96, 6)


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _run_good_sample(db):
    job = Job(
        sample_id=None,
        sample_name="demo-good-r1",
        status="pending",
        created_by="bioops",
        fastq_snapshot=GOOD_FASTQ,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    create_job_stages(db, job.id)
    return run_pipeline_sync(db, job)


def _assert_real_three_metrics(metrics):
    assert metrics is not None
    assert "placeholder" not in metrics
    assert metrics["reads"] == EXPECTED_READS
    assert isinstance(metrics["mean_quality"], (int, float))
    assert metrics["mean_quality"] > 0
    assert metrics["n_rate"] == EXPECTED_N_RATE


def test_success_persists_real_three_metrics():
    db = _make_db()
    try:
        job = _run_good_sample(db)
        assert job.status == "success"
        _assert_real_three_metrics(job.metrics)
        # 落库值与汇总视图一致
        assert job.metrics["summary"]["reads"] == EXPECTED_READS
        assert job.metrics["summary"]["mean_quality"] == job.metrics["mean_quality"]
        assert job.metrics["summary"]["n_rate"] == EXPECTED_N_RATE
    finally:
        db.close()


def test_get_job_returns_same_real_metrics():
    db = _make_db()
    try:
        job = _run_good_sample(db)

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        try:
            client = TestClient(app)
            token = create_access_token("bioops", "bioops")
            resp = client.get(
                f"/api/jobs/{job.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        _assert_real_three_metrics(body["metrics"])
        # 接口读回值与落库值完全一致（读路径不再改写）
        assert body["metrics"]["reads"] == job.metrics["reads"]
        assert body["metrics"]["mean_quality"] == job.metrics["mean_quality"]
        assert body["metrics"]["n_rate"] == job.metrics["n_rate"]
    finally:
        db.close()
