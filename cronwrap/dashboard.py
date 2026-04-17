"""Terminal dashboard: summary of all jobs across metrics, schedule, and overdue status."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import datetime

from cronwrap.metrics import get_all_job_metrics, JobMetrics
from cronwrap.overdue import check_all_jobs, OverdueReport


@dataclass
class DashboardRow:
    job_name: str
    total_runs: int
    success_rate: float  # 0.0 – 1.0
    avg_duration: float
    last_exit: Optional[int]
    overdue: bool
    next_run: Optional[datetime.datetime]


def build_dashboard(db_path: str, jobs: list) -> List[DashboardRow]:
    """Combine metrics and overdue info into dashboard rows."""
    metrics: dict[str, JobMetrics] = {m.job_name: m for m in get_all_job_metrics(db_path)}
    overdue_map: dict[str, OverdueReport] = {r.job_name: r for r in check_all_jobs(jobs, db_path)}

    rows: List[DashboardRow] = []
    seen = set()

    for m in metrics.values():
        od = overdue_map.get(m.job_name)
        rate = m.success_count / m.total_runs if m.total_runs else 0.0
        rows.append(DashboardRow(
            job_name=m.job_name,
            total_runs=m.total_runs,
            success_rate=rate,
            avg_duration=m.avg_duration,
            last_exit=m.last_exit_code,
            overdue=od.overdue if od else False,
            next_run=od.next_run if od else None,
        ))
        seen.add(m.job_name)

    for od in overdue_map.values():
        if od.job_name not in seen:
            rows.append(DashboardRow(
                job_name=od.job_name,
                total_runs=0,
                success_rate=0.0,
                avg_duration=0.0,
                last_exit=None,
                overdue=od.overdue,
                next_run=od.next_run,
            ))

    rows.sort(key=lambda r: r.job_name)
    return rows


def render_dashboard(rows: List[DashboardRow]) -> str:
    if not rows:
        return "No job data available.\n"
    header = f"{'JOB':<30} {'RUNS':>6} {'SUCCESS%':>9} {'AVG(s)':>7} {'LAST':>5} {'OVERDUE':>8} {'NEXT RUN'}"
    lines = [header, "-" * len(header)]
    for r in rows:
        pct = f"{r.success_rate * 100:.1f}%"
        avg = f"{r.avg_duration:.2f}"
        last = str(r.last_exit) if r.last_exit is not None else "--"
        od = "YES" if r.overdue else "no"
        nxt = r.next_run.strftime("%Y-%m-%d %H:%M") if r.next_run else "--"
        lines.append(f"{r.job_name:<30} {r.total_runs:>6} {pct:>9} {avg:>7} {last:>5} {od:>8} {nxt}")
    return "\n".join(lines) + "\n"


def print_dashboard(rows: List[DashboardRow]) -> None:
    print(render_dashboard(rows))
