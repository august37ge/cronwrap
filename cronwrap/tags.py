"""Tag-based filtering and grouping for cron jobs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TagIndex:
    """Maps tags to job names."""
    index: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, job_name: str, tags: List[str]) -> None:
        for tag in tags:
            self.index.setdefault(tag, []).append(job_name)

    def jobs_for_tag(self, tag: str) -> List[str]:
        return list(self.index.get(tag, []))

    def all_tags(self) -> List[str]:
        return sorted(self.index.keys())


def build_tag_index(jobs: List[dict]) -> TagIndex:
    """Build a TagIndex from a list of job config dicts."""
    idx = TagIndex()
    for job in jobs:
        name = job.get("name", "")
        tags = job.get("tags", [])
        if name and tags:
            idx.add(name, tags)
    return idx


def filter_jobs_by_tag(jobs: List[dict], tag: str) -> List[dict]:
    """Return only jobs that include the given tag."""
    return [j for j in jobs if tag in j.get("tags", [])]


def filter_jobs_by_tags(jobs: List[dict], tags: List[str], match_all: bool = False) -> List[dict]:
    """Filter jobs by multiple tags.

    Args:
        jobs: list of job config dicts.
        tags: tags to filter by.
        match_all: if True, job must have ALL tags; otherwise ANY tag suffices.
    """
    if not tags:
        return jobs
    if match_all:
        return [j for j in jobs if all(t in j.get("tags", []) for t in tags)]
    return [j for j in jobs if any(t in j.get("tags", []) for t in tags)]
