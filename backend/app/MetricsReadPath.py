from app.MetricsDropBypass import read_metrics


def prepare_job_metrics(job) -> None:
    if job is not None and getattr(job, "metrics", None) is not None:
        job.metrics = read_metrics(job.metrics)
