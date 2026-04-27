"""Pipeline support: run a sequence of jobs where each step depends on the previous."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.runner import RunResult, run_command


@dataclass
class PipelineStep:
    name: str
    command: str
    timeout: Optional[float] = None
    retries: int = 0


@dataclass
class StepOutcome:
    step: PipelineStep
    result: RunResult
    attempt: int = 1

    @property
    def succeeded(self) -> bool:
        return self.result.returncode == 0


@dataclass
class PipelineResult:
    pipeline_name: str
    outcomes: List[StepOutcome] = field(default_factory=list)
    aborted_at: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return all(o.succeeded for o in self.outcomes) and self.aborted_at is None

    @property
    def total_duration(self) -> float:
        return sum(o.result.duration for o in self.outcomes)


def run_pipeline(name: str, steps: List[PipelineStep]) -> PipelineResult:
    """Execute steps sequentially; abort on first failure."""
    result = PipelineResult(pipeline_name=name)
    for step in steps:
        outcome = _run_step(step)
        result.outcomes.append(outcome)
        if not outcome.succeeded:
            result.aborted_at = step.name
            break
    return result


def _run_step(step: PipelineStep) -> StepOutcome:
    last: Optional[RunResult] = None
    for attempt in range(1, step.retries + 2):
        last = run_command(step.command, timeout=step.timeout)
        if last.returncode == 0:
            return StepOutcome(step=step, result=last, attempt=attempt)
        if attempt <= step.retries:
            time.sleep(0.1)
    assert last is not None
    return StepOutcome(step=step, result=last, attempt=step.retries + 1)


def render_pipeline_result(result: PipelineResult) -> str:
    lines = [f"Pipeline: {result.pipeline_name}"]
    for o in result.outcomes:
        status = "OK" if o.succeeded else "FAIL"
        lines.append(
            f"  [{status}] {o.step.name}  "
            f"exit={o.result.returncode}  "
            f"duration={o.result.duration:.2f}s  "
            f"attempt={o.attempt}"
        )
    if result.aborted_at:
        lines.append(f"  Aborted at step: {result.aborted_at}")
    lines.append(f"  Total duration: {result.total_duration:.2f}s")
    lines.append(f"  Result: {'SUCCESS' if result.succeeded else 'FAILURE'}")
    return "\n".join(lines)
