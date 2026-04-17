"""Human-readable report for retention / pruning operations."""
from __future__ import annotations

from cronwrap.retention import PruneResult


def render_prune_result(result: PruneResult) -> str:
    job_label = result.job_name if result.job_name else "<all jobs>"
    cutoff_str = result.cutoff.strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"Pruned {result.rows_deleted} record(s) for '{job_label}' "
        f"(cutoff: {cutoff_str})"
    )


def render_prune_results(results: list[PruneResult]) -> str:
    if not results:
        return "No jobs pruned."
    lines = [render_prune_result(r) for r in results]
    total = sum(r.rows_deleted for r in results)
    lines.append(f"Total records deleted: {total}")
    return "\n".join(lines)


def print_prune_report(results: list[PruneResult]) -> None:
    print(render_prune_results(results))
