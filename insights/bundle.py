"""Evidence bundle loader.

The on-disk schema (JSON) is intentionally aligned with the bundles produced
by the upstream CSW-API-Compliance-Automation tooling so we can consume them
unchanged and add executive-flavor renderings on top.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EvidenceBundle:
    """In-memory view of a tenant evidence bundle.

    Only the fields the renderers actually consume are surfaced here; the raw
    payload remains available via ``.raw`` for advanced or future use cases.
    """

    tenant: str
    generated_at: str
    cluster_url: str
    raw: dict[str, Any]

    # Operational counts
    workloads_total: int = 0
    workloads_with_agent: int = 0
    scopes_total: int = 0
    policies_total: int = 0
    policies_enforced: int = 0
    policies_absolute: int = 0
    vulnerabilities_critical: int = 0
    vulnerabilities_high: int = 0
    vulnerabilities_medium: int = 0
    enforcement_alerts_24h: int = 0

    # Per-framework coverage as recorded in the bundle (control_id -> status)
    framework_coverage: dict[str, dict[str, str]] = field(default_factory=dict)

    @property
    def agent_coverage_pct(self) -> float:
        if self.workloads_total == 0:
            return 0.0
        return 100.0 * self.workloads_with_agent / self.workloads_total

    @property
    def enforcement_pct(self) -> float:
        if self.policies_total == 0:
            return 0.0
        return 100.0 * self.policies_enforced / self.policies_total


def load_bundle(path: Path | str) -> EvidenceBundle:
    """Load and validate an evidence bundle JSON file."""

    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Evidence bundle not found: {p}")

    raw = json.loads(p.read_text(encoding="utf-8"))

    meta = raw.get("metadata", {})
    counts = raw.get("counts", {})
    vulns = counts.get("vulnerabilities", {})

    return EvidenceBundle(
        tenant=meta.get("tenant", p.parent.parent.name),
        generated_at=meta.get("generated_at", ""),
        cluster_url=meta.get("cluster_url", ""),
        raw=raw,
        workloads_total=counts.get("workloads_total", 0),
        workloads_with_agent=counts.get("workloads_with_agent", 0),
        scopes_total=counts.get("scopes", 0),
        policies_total=counts.get("policies_total", 0),
        policies_enforced=counts.get("policies_enforced", 0),
        policies_absolute=counts.get("policies_absolute", 0),
        vulnerabilities_critical=vulns.get("critical", 0),
        vulnerabilities_high=vulns.get("high", 0),
        vulnerabilities_medium=vulns.get("medium", 0),
        enforcement_alerts_24h=counts.get("enforcement_alerts_24h", 0),
        framework_coverage=raw.get("framework_coverage", {}),
    )
