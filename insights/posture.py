"""Posture scoring (0-100) for a CSW tenant.

Scoring rationale (deliberately transparent so reviewers can argue with it):

  * Visibility   : 25 pts  - agents on workloads, scope discipline
  * Segmentation : 30 pts  - policies authored, enforcement enabled, absolute coverage
  * Hygiene      : 20 pts  - vulnerability burden weighted by severity
  * Operations   : 15 pts  - enforcement alerts cleared, alert noise
  * Compliance   :  10 pts - per-framework coverage breadth

Each component is normalised to its own ceiling, then summed. The breakdown
ships with the score so executives can see *why*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .bundle import EvidenceBundle

Grade = Literal["A", "B", "C", "D", "F"]

# Scoring component ceilings - fixed contract used by the renderers.
WEIGHT_VISIBILITY = 25
WEIGHT_SEGMENTATION = 30
WEIGHT_HYGIENE = 20
WEIGHT_OPERATIONS = 15
WEIGHT_COMPLIANCE = 10

# Vulnerability burden caps (anything beyond is treated as "saturated bad")
VULN_CAP_CRITICAL = 25
VULN_CAP_HIGH = 100

# Operational health: > N alerts/24h treated as saturated noise
ALERT_NOISE_CAP = 200


@dataclass
class PostureScore:
    total: int
    grade: Grade
    components: dict[str, int] = field(default_factory=dict)
    rationale: dict[str, str] = field(default_factory=dict)


def _grade(total: int) -> Grade:
    if total >= 90:
        return "A"
    if total >= 80:
        return "B"
    if total >= 70:
        return "C"
    if total >= 60:
        return "D"
    return "F"


def score_posture(b: EvidenceBundle) -> PostureScore:
    """Compute a 0-100 posture score from an evidence bundle."""

    components: dict[str, int] = {}
    rationale: dict[str, str] = {}

    # ---- Visibility (25) ----
    coverage = b.agent_coverage_pct / 100.0
    visibility = round(WEIGHT_VISIBILITY * coverage)
    components["visibility"] = visibility
    rationale["visibility"] = (
        f"{b.workloads_with_agent}/{b.workloads_total} workloads reporting "
        f"({b.agent_coverage_pct:.1f}% agent coverage)."
    )

    # ---- Segmentation (30) ----
    if b.policies_total == 0:
        seg = 0
        seg_text = "No policies authored - segmentation foundation not in place."
    else:
        enforced = b.policies_enforced / b.policies_total
        absolute = b.policies_absolute / b.policies_total
        seg = round(WEIGHT_SEGMENTATION * (0.7 * enforced + 0.3 * absolute))
        seg_text = (
            f"{b.policies_total} policies, {b.policies_enforced} in enforce mode "
            f"({enforced * 100:.0f}%), {b.policies_absolute} absolute "
            f"({absolute * 100:.0f}%)."
        )
    components["segmentation"] = seg
    rationale["segmentation"] = seg_text

    # ---- Hygiene (20) - vulnerability burden ----
    crit = min(b.vulnerabilities_critical, VULN_CAP_CRITICAL) / VULN_CAP_CRITICAL
    high = min(b.vulnerabilities_high, VULN_CAP_HIGH) / VULN_CAP_HIGH
    burden = 0.7 * crit + 0.3 * high
    hygiene = round(WEIGHT_HYGIENE * (1 - burden))
    components["hygiene"] = hygiene
    rationale["hygiene"] = (
        f"{b.vulnerabilities_critical} critical, {b.vulnerabilities_high} high CVEs "
        f"detected on workloads."
    )

    # ---- Operations (15) - alert hygiene ----
    noise = min(b.enforcement_alerts_24h, ALERT_NOISE_CAP) / ALERT_NOISE_CAP
    operations = round(WEIGHT_OPERATIONS * (1 - noise))
    components["operations"] = operations
    rationale["operations"] = (
        f"{b.enforcement_alerts_24h} enforcement alerts in last 24h."
    )

    # ---- Compliance (10) - framework breadth ----
    fw_total = sum(len(v) for v in b.framework_coverage.values()) or 1
    fw_met = sum(
        1
        for ctrls in b.framework_coverage.values()
        for status in ctrls.values()
        if status.lower() == "met"
    )
    compliance = round(WEIGHT_COMPLIANCE * (fw_met / fw_total))
    components["compliance"] = compliance
    rationale["compliance"] = (
        f"{fw_met}/{fw_total} controls marked 'met' across "
        f"{len(b.framework_coverage)} frameworks."
    )

    total = sum(components.values())
    return PostureScore(
        total=total,
        grade=_grade(total),
        components=components,
        rationale=rationale,
    )
