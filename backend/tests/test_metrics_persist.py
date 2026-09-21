"""合格样例跑完后,reads / mean_quality / n_rate 必须以真实数值落库。

复验场景:好样例(demo-good-r1 同一份 data/good.fastq)执行成功,
刷新(重新查询)后三指标仍为真值,不允许出现占位数据。
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Job
from app.pipeline.runner import create_job_stages, run_pipeline_sync


GOOD_FASTQ = (Path(__file__).resolve().parent.parent / "data" / "good.fastq").read_text(
    encoding="utf-8"
)

# good.fastq:3 条读段 × 32 碱基;仅第 3 条含 2 个 N
EXPECTED_READS = 3
EXPECTED_N_RATE = round(2 / 96, 6)  # 0.020833
EXPECTED_MEAN_Q = 3834 / 96  # 39.9375


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


def _new_job(db, fastq_text: str) -> Job:
    job = Job(
        sample_id=None,
        sample_name="demo-good-r1",
        status="pending",
        created_by="bioops",
        fastq_snapshot=fastq_text,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    create_job_stages(db, job.id)
    return job


def test_success_persists_real_metrics(db_session):
    job = run_pipeline_sync(db_session, _new_job(db_session, GOOD_FASTQ))

    assert job.status == "success"
    assert job.error_message is None

    m = job.metrics
    assert m is not None, "成功作业必须落库指标"
    assert "placeholder" not in m, "禁止占位数据落库"

    # 三指标为真实数值
    assert m["reads"] == EXPECTED_READS
    assert m["mean_quality"] == pytest.approx(EXPECTED_MEAN_Q, abs=1e-3)
    assert m["mean_quality"] > 0
    assert m["n_rate"] == pytest.approx(EXPECTED_N_RATE, abs=1e-6)

    # 汇总与顶层一致(卡面与接口一致的数据基础)
    summary = m["summary"]
    assert summary["reads"] == m["reads"]
    assert summary["mean_quality"] == m["mean_quality"]
    assert summary["n_rate"] == m["n_rate"]


def test_metrics_survive_reread_after_refresh(db_session):
    """模拟详情页刷新:重新从库里查出,三指标仍为真值。"""
    job = run_pipeline_sync(db_session, _new_job(db_session, GOOD_FASTQ))
    job_id = job.id
    db_session.expunge_all()

    fresh = db_session.query(Job).filter(Job.id == job_id).first()
    assert fresh.status == "success"
    assert fresh.metrics is not None
    assert "placeholder" not in fresh.metrics
    assert fresh.metrics["reads"] == EXPECTED_READS
    assert fresh.metrics["mean_quality"] == pytest.approx(EXPECTED_MEAN_Q, abs=1e-3)
    assert fresh.metrics["n_rate"] == pytest.approx(EXPECTED_N_RATE, abs=1e-6)
