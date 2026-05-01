"""Top risks extraction.

A "risk" is anything that, if not addressed, materially weakens the posture
score. Risks are sorted by impact (estimated score uplift if addressed) so the
CISO flavor can show "fix these 5 things and your score moves N points."
"""

from __future__ import annotations

from dataclasses import dataclass

from .bundle import EvidenceBundle


@dataclass
class Risk:
    title: str
    detail: str
    impact_points: int
    category: str  # visibility | segmentation | hygiene | operations | compliance


def top_risks(b: EvidenceBundle, limit: int = 5) -> list[Risk]:
    risks: list[Risk] = []

    # Visibility gaps
    missing = b.workloads_total - b.workloads_with_agent
    if missing > 0 and b.workloads_total > 0:
        gap_pct = 100 * missing / b.workloads_total
        impact = max(1, round(25 * (gap_pct / 100)))
        risks.append(
            Risk(
                title=f"{missing} workloads without an agent",
                detail=(
                    f"Workloads outside agent coverage are invisible to flow "
                    f"analytics, ADM, and policy enforcement. Closing this gap "
                    f"unlocks visibility-driven controls in every framework."
                ),
                impact_points=impact,
                category="visibility",
            )
        )

    # Segmentation gaps
    unenforced = b.policies_total - b.policies_enforced
    if unenforced > 0:
        impact = max(1, round(15 * (unenforced / max(b.policies_total, 1))))
        risks.append(
            Risk(
                title=f"{unenforced} policies remain in monitor mode",
                detail=(
                    "Monitor-mode policies generate evidence but do not block "
                    "lateral movement. Promoting reviewed policies to enforce "
                    "directly improves the segmentation score component."
                ),
                impact_points=impact,
                category="segmentation",
            )
        )

    if b.policies_total > 0 and b.policies_absolute / b.policies_total < 0.2:
        risks.append(
            Risk(
                title="Few absolute policies in place",
                detail=(
                    "Absolute policies are the right tool for crown-jewel "
                    "isolation (PHI, cardholder data, regulated systems). "
                    "Their absence indicates the segmentation strategy is "
                    "still permissive-by-default."
                ),
                impact_points=6,
                category="segmentation",
            )
        )

    # Hygiene
    if b.vulnerabilities_critical > 0:
        impact = min(14, max(2, b.vulnerabilities_critical // 2))
        risks.append(
            Risk(
                title=f"{b.vulnerabilities_critical} critical CVEs on workloads",
                detail=(
                    "CSW correlates package CVEs to running processes. Each "
                    "critical CVE on an internet-reachable workload is a "
                    "candidate for escalation to patching or compensating "
                    "policy."
                ),
                impact_points=impact,
                category="hygiene",
            )
        )

    # Operations
    if b.enforcement_alerts_24h > ALERT_THRESHOLD:
        risks.append(
            Risk(
                title=f"{b.enforcement_alerts_24h} enforcement alerts in 24h",
                detail=(
                    "Sustained alert volume indicates either policy gaps "
                    "(legitimate flows blocked) or active attack pressure. "
                    "Both warrant SOC engagement and policy review."
                ),
                impact_points=5,
                category="operations",
            )
        )

    # Compliance breadth
    for fw, ctrls in b.framework_coverage.items():
        if not ctrls:
            continue
        unmet = sum(1 for s in ctrls.values() if s.lower() != "met")
        if unmet >= 3:
            risks.append(
                Risk(
                    title=f"{fw}: {unmet} controls not marked met",
                    detail=(
                        f"{unmet} controls in the {fw} catalog still show "
                        f"partial or pending evidence. Address these before "
                        f"the next audit cycle."
                    ),
                    impact_points=2,
                    category="compliance",
                )
            )

    risks.sort(key=lambda r: r.impact_points, reverse=True)
    return risks[:limit]


ALERT_THRESHOLD = 50
