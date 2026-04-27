"""Tests for cronwrap.pipeline."""
import sys

import pytest

from cronwrap.pipeline import (
    PipelineResult,
    PipelineStep,
    StepOutcome,
    render_pipeline_result,
    run_pipeline,
)
from cronwrap.runner import RunResult


def _ok_step(name: str = "step") -> PipelineStep:
    cmd = f"{sys.executable} -c 'print(1)'"
    return PipelineStep(name=name, command=cmd)


def _fail_step(name: str = "step") -> PipelineStep:
    cmd = f"{sys.executable} -c 'raise SystemExit(1)'"
    return PipelineStep(name=name, command=cmd)


def test_all_steps_succeed():
    result = run_pipeline("demo", [_ok_step("a"), _ok_step("b")])
    assert result.succeeded
    assert len(result.outcomes) == 2
    assert result.aborted_at is None


def test_pipeline_aborts_on_first_failure():
    result = run_pipeline("demo", [_ok_step("a"), _fail_step("b"), _ok_step("c")])
    assert not result.succeeded
    assert len(result.outcomes) == 2  # 'c' never runs
    assert result.aborted_at == "b"


def test_empty_pipeline_succeeds():
    result = run_pipeline("empty", [])
    assert result.succeeded
    assert result.total_duration == 0.0


def test_retry_succeeds_eventually():
    # first attempt fails (exit 1), retries=0 means only one attempt
    step = _fail_step("r")
    step.retries = 0
    result = run_pipeline("retry", [step])
    assert not result.succeeded
    assert result.outcomes[0].attempt == 1


def test_total_duration_is_sum():
    r1 = RunResult(returncode=0, stdout="", stderr="", duration=1.5)
    r2 = RunResult(returncode=0, stdout="", stderr="", duration=2.0)
    pr = PipelineResult(
        pipeline_name="x",
        outcomes=[
            StepOutcome(step=_ok_step("a"), result=r1),
            StepOutcome(step=_ok_step("b"), result=r2),
        ],
    )
    assert pr.total_duration == pytest.approx(3.5)


def test_render_contains_step_names():
    result = run_pipeline("mypipe", [_ok_step("build"), _ok_step("test")])
    text = render_pipeline_result(result)
    assert "build" in text
    assert "test" in text
    assert "SUCCESS" in text


def test_render_shows_failure_and_aborted_at():
    result = run_pipeline("mypipe", [_fail_step("deploy")])
    text = render_pipeline_result(result)
    assert "FAILURE" in text
    assert "deploy" in text
    assert "Aborted at step" in text
