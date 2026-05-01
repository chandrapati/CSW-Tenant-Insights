"""Top wins extraction.

Wins are the positive narrative for both flavors: "you already have these
controls in place." They give CISOs ammunition for board updates and give SEs
something concrete to celebrate before pivoting to gaps in a POV.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bundle import EvidenceBundle


@dataclass
class Win:
    title: str
    detail: str


HIGH_AGENT_COVERAGE = 90.0
GOOD_ENFORCEMENT_RATIO = 0.6


def top_wins(b: EvidenceBundle, limit: int = 5) -> list[Win]:
    wins: list[Win] = []

    if b.agent_coverage_pct >= HIGH_AGENT_COVERAGE:
        wins.append(
            Win(
                title=f"Agent coverage at {b.agent_coverage_pct:.1f}%",
                detail=(
                    "Strong agent coverage means flow analytics, ADM "
                    "recommendations, and policy enforcement are operating "
                    "on the real estate, not a sample."
                ),
            )
        )

    if b.policies_total >= 100:
        wins.append(
            Win(
                title=f"{b.policies_total} policies authored",
                detail=(
                    "A populated policy library indicates segmentation "
                    "is past initial discovery and into active design."
                ),
            )
        )

    if (
        b.policies_total > 0
        and b.policies_enforced / b.policies_total >= GOOD_ENFORCEMENT_RATIO
    ):
        ratio = b.policies_enforced / b.policies_total
        wins.append(
            Win(
                title=f"{ratio * 100:.0f}% of policies in enforce mode",
                detail=(
                    "Enforcement-mode policies are the difference between "
                    "an audit narrative and a control. This ratio is the "
                    "single best evidence the program is operational."
                ),
            )
        )

    if b.scopes_total >= 20:
        wins.append(
            Win(
                title=f"{b.scopes_total} scopes defined",
                detail=(
                    "A scope hierarchy this deep means the segmentation "
                    "model reflects organisational reality - prerequisite "
                    "for least-privilege at scale."
                ),
            )
        )

    fw_with_evidence = sum(1 for ctrls in b.framework_coverage.values() if ctrls)
    if fw_with_evidence >= 3:
        wins.append(
            Win(
                title=f"Evidence collected for {fw_with_evidence} frameworks",
                detail=(
                    "Re-using a single set of CSW evidence across multiple "
                    "frameworks is the headline value proposition - this "
                    "tenant is realising it."
                ),
            )
        )

    return wins[:limit]
