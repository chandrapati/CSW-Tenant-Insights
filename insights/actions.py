"""30-day action plan generation.

The action plan is the bridge between "what's wrong" (risks) and "what to do"
(scheduled work the customer's team can put in their next sprint). Each action
maps to one or more risks so the CISO flavor can answer "if I approve these,
what changes."
"""

from __future__ import annotations

from dataclasses import dataclass

from .bundle import EvidenceBundle
from .risks import Risk


@dataclass
class Action:
    week: int
    title: str
    owner: str
    detail: str
    addresses: list[str]


def action_plan(b: EvidenceBundle, risks: list[Risk]) -> list[Action]:
    """Sequence the top risks into a 4-week plan with owners and crisp asks."""

    plan: list[Action] = []
    week = 1

    risks_by_category: dict[str, list[Risk]] = {}
    for r in risks:
        risks_by_category.setdefault(r.category, []).append(r)

    if "visibility" in risks_by_category:
        for r in risks_by_category["visibility"][:1]:
            plan.append(
                Action(
                    week=week,
                    title="Close agent-coverage gap",
                    owner="Platform Engineering",
                    detail=(
                        f"Identify the {b.workloads_total - b.workloads_with_agent} "
                        f"workloads without an agent. Triage into: (a) deploy now, "
                        f"(b) excluded by policy, (c) decommission. Track in a "
                        f"single ticket; aim for 95%+ coverage."
                    ),
                    addresses=[r.title],
                )
            )
            week += 1

    if "segmentation" in risks_by_category:
        for r in risks_by_category["segmentation"][:2]:
            if "monitor mode" in r.title:
                plan.append(
                    Action(
                        week=week,
                        title="Promote vetted policies to enforce mode",
                        owner="Security Operations",
                        detail=(
                            "Run the 30-day flow review on monitor-mode "
                            "policies for top 3 scopes. Promote those with "
                            "no false-positive flow violations to enforce."
                        ),
                        addresses=[r.title],
                    )
                )
                week += 1
            elif "absolute" in r.title.lower():
                plan.append(
                    Action(
                        week=week,
                        title="Author absolute policies for crown jewels",
                        owner="Security Architecture",
                        detail=(
                            "Identify the top 3 crown-jewel scopes "
                            "(databases of regulated data, payment systems, "
                            "PHI stores). Draft absolute policies that take "
                            "precedence over inherited rules."
                        ),
                        addresses=[r.title],
                    )
                )
                week += 1

    if "hygiene" in risks_by_category:
        for r in risks_by_category["hygiene"][:1]:
            plan.append(
                Action(
                    week=week,
                    title="Address top critical CVEs",
                    owner="Vulnerability Management",
                    detail=(
                        "Pull the CSW vulnerability dashboard, sort by "
                        "internet exposure + severity, dispatch top 10 to "
                        "patching or compensating-policy workstreams."
                    ),
                    addresses=[r.title],
                )
            )
            week += 1

    if "operations" in risks_by_category:
        for r in risks_by_category["operations"][:1]:
            plan.append(
                Action(
                    week=week,
                    title="Tune enforcement alert noise",
                    owner="Security Operations",
                    detail=(
                        "Categorise the past 24h of alerts (legitimate "
                        "block, missing exception, real attack). Build "
                        "exception rules for the first two; route the third "
                        "into incident response."
                    ),
                    addresses=[r.title],
                )
            )
            week += 1

    refresh_week = max(week, 4)
    plan.append(
        Action(
            week=refresh_week,
            title="Refresh evidence and report",
            owner="Compliance / GRC",
            detail=(
                "Re-run csw-insights against the tenant. Compare posture "
                "score to baseline; share delta with steering committee."
            ),
            addresses=[],
        )
    )
    return plan
