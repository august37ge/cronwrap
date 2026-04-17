"""Tests for cronwrap.tags."""
import pytest
from cronwrap.tags import TagIndex, build_tag_index, filter_jobs_by_tag, filter_jobs_by_tags

JOBS = [
    {"name": "backup", "tags": ["daily", "storage"]},
    {"name": "report", "tags": ["daily", "email"]},
    {"name": "cleanup", "tags": ["storage"]},
    {"name": "ping", "tags": []},
]


def test_build_tag_index():
    idx = build_tag_index(JOBS)
    assert set(idx.jobs_for_tag("daily")) == {"backup", "report"}
    assert set(idx.jobs_for_tag("storage")) == {"backup", "cleanup"}
    assert idx.jobs_for_tag("email") == ["report"]
    assert idx.jobs_for_tag("missing") == []


def test_all_tags_sorted():
    idx = build_tag_index(JOBS)
    assert idx.all_tags() == ["daily", "email", "storage"]


def test_filter_by_single_tag():
    result = filter_jobs_by_tag(JOBS, "storage")
    names = [j["name"] for j in result]
    assert set(names) == {"backup", "cleanup"}


def test_filter_by_unknown_tag():
    assert filter_jobs_by_tag(JOBS, "nope") == []


def test_filter_by_tags_any():
    result = filter_jobs_by_tags(JOBS, ["email", "storage"])
    names = {j["name"] for j in result}
    assert names == {"backup", "report", "cleanup"}


def test_filter_by_tags_all():
    result = filter_jobs_by_tags(JOBS, ["daily", "storage"], match_all=True)
    names = [j["name"] for j in result]
    assert names == ["backup"]


def test_filter_empty_tags_returns_all():
    assert filter_jobs_by_tags(JOBS, []) == JOBS


def test_tag_index_add():
    idx = TagIndex()
    idx.add("myjob", ["a", "b"])
    assert "myjob" in idx.jobs_for_tag("a")
    assert "myjob" in idx.jobs_for_tag("b")
