"""Top wins extraction.

Wins are the positive narrative for both flavors: "you already have these
controls in place." They give CISOs ammunition for board updates and give SEs
something concrete to celebrate before pivoting to gaps in a POV.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .bundle import EvidenceBundle
from .framework_map import CATEGORY_IMPACT, FrameworkImpact


@dataclass
class Win:
    title: str
    detail: str
    category: str = ""
    framework_impacts: list[FrameworkImpact] = field(default_factory=list)

    def affects_summary(self) -> str:
        if not self.framework_impacts:
            return "—"
        return "; ".join(fi.summary() for fi in self.framework_impacts)


HIGH_AGENT_COVERAGE = 90.0
GOOD_ENFORCEMENT_RATIO = 0.6


def _met_impacts(category: str, fw_cov: dict[str, dict[str, str]]) -> list[FrameworkImpact]:
    """Subset of category impacts whose controls are marked met in this tenant."""
    out: list[FrameworkImpact] = []
    for fw, ctrl_pairs in CATEGORY_IMPACT.get(category, {}).items():
        present = fw_cov.get(fw)
        if not present:
            continue
        controls = [
            (cid, why)
            for cid, why in ctrl_pairs
            if present.get(cid, "").lower() == "met"
        ]
        if controls:
            out.append(FrameworkImpact(framework=fw, controls=controls))
    return out


def top_wins(b: EvidenceBundle, limit: int = 5) -> list[Win]:
    wins: list[Win] = []
    fw_cov = b.framework_coverage

    if b.agent_coverage_pct >= HIGH_AGENT_COVERAGE:
        wins.append(
            Win(
                title=f"Agent coverage at {b.agent_coverage_pct:.1f}%",
                detail=(
                    "Strong agent coverage means flow analytics, ADM "
                    "recommendations, and policy enforcement are operating "
                    "on the real estate, not a sample."
                ),
                category="visibility",
                framework_impacts=_met_impacts("visibility", fw_cov),
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
                category="segmentation",
                framework_impacts=_met_impacts("segmentation", fw_cov),
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
                category="segmentation",
                framework_impacts=_met_impacts("segmentation", fw_cov),
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
                category="visibility",
                framework_impacts=_met_impacts("visibility", fw_cov),
            )
        )

    fw_with_evidence = sum(1 for ctrls in b.framework_coverage.values() if ctrls)
    if fw_with_evidence >= 3:
        # Single FrameworkImpact per evaluated framework, listing the controls
        # already met — gives the CISO concrete evidence per framework.
        impacts = []
        for fw, ctrls in b.framework_coverage.items():
            met = [(cid, "marked met in this collection") for cid, s in ctrls.items() if s.lower() == "met"]
            if met:
                impacts.append(FrameworkImpact(framework=fw, controls=met))
        wins.append(
            Win(
                title=f"Evidence collected for {fw_with_evidence} frameworks",
                detail=(
                    "Re-using a single set of CSW evidence across multiple "
                    "frameworks is the headline value proposition - this "
                    "tenant is realising it."
                ),
                category="compliance",
                framework_impacts=impacts,
            )
        )

    return wins[:limit]
