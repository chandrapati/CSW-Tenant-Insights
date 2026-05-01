"""Map insight categories to the framework controls they typically affect.

This is the "and here's why this matters for your auditors" layer. A risk
in `visibility` doesn't just cost posture points; it has knock-on impact
on specific HIPAA / PCI / NIST controls that depend on knowing what's in
the estate. Surfacing those linkages turns abstract posture math into a
compliance conversation.

The mappings here are deliberately conservative: each category lists the
controls where the cited capability is a *primary* contributor (not just
"helps a little"). Reviewers can argue with each row in isolation, which
is the point.

When the renderer fills in the report, it intersects this map with the
bundle's `framework_coverage` so only frameworks the tenant actually
evaluates show up — and for risks, only controls not yet marked `met`
are listed (because those are the ones the action would help close).
"""

from __future__ import annotations

# category -> framework -> [(control_id, why_it_applies), ...]
#
# Keep `why_it_applies` short; the renderer composes it into a sentence.
CATEGORY_IMPACT: dict[str, dict[str, list[tuple[str, str]]]] = {
    "visibility": {
        "HIPAA": [
            ("164.308(a)(1)(ii)(A)", "risk analysis requires knowing what's in scope"),
            ("164.310(c)", "workstation security depends on inventory"),
        ],
        "PCI-DSS": [
            ("1.2.1", "network controls depend on knowing what they protect"),
            ("11.3", "penetration-test scope is set by inventory"),
        ],
        "NIST-800-53": [
            ("AU-2", "audit events presume coverage of every workload"),
            ("SI-4", "system monitoring requires telemetry from every workload"),
        ],
        "DORA": [
            ("Art.8", "ICT risk management requires complete asset inventory"),
            ("Art.9", "ICT security depends on knowing the estate"),
        ],
        "SOC2": [
            ("CC6.1", "logical access requires knowing the systems in scope"),
            ("CC7.2", "system monitoring requires complete telemetry"),
        ],
    },
    "segmentation": {
        "HIPAA": [
            ("164.308(a)(4)", "information access management is enforced via policy"),
            ("164.312(a)(1)", "access control is implemented as policy"),
            ("164.312(e)(1)", "transmission security relies on segmentation"),
        ],
        "PCI-DSS": [
            ("1.2.1", "network security controls are the segmentation evidence"),
            ("1.3", "no direct internet access to CDE requires enforced policy"),
            ("12.5.3", "segmentation effectiveness is tested annually"),
        ],
        "NIST-800-53": [
            ("AC-3", "access enforcement is implemented as policy"),
            ("AC-4", "information flow enforcement is the segmentation control"),
            ("CM-7", "least functionality limits flows to what is needed"),
            ("SC-7", "boundary protection is segmentation"),
            ("SC-7(5)", "deny-by-default requires absolute policies"),
        ],
        "DORA": [
            ("Art.9", "ICT security includes segmentation of critical assets"),
        ],
        "SOC2": [
            ("CC6.1", "logical access is implemented as enforced policy"),
            ("CC6.6", "boundary protection is segmentation in cloud workloads"),
        ],
    },
    "hygiene": {
        "HIPAA": [
            ("164.308(a)(1)(ii)(A)", "risk analysis includes vulnerability state"),
        ],
        "PCI-DSS": [
            ("6.4.2", "production systems must be protected from known CVEs"),
            ("11.3", "vulnerability scanning evidence drives this control"),
        ],
        "NIST-800-53": [
            ("RA-5", "vulnerability scanning and remediation"),
        ],
        "DORA": [
            ("Art.10", "detection of ICT vulnerabilities"),
        ],
        "SOC2": [
            ("CC7.1", "vulnerability detection feeds incident response"),
        ],
    },
    "operations": {
        "HIPAA": [
            ("164.308(a)(5)(ii)(B)", "security incident procedures depend on alert hygiene"),
        ],
        "PCI-DSS": [
            ("10.2", "logging requirements include enforcement events"),
        ],
        "NIST-800-53": [
            ("AU-2", "audit events include enforcement actions"),
            ("SI-4", "system monitoring includes alert response"),
        ],
        "DORA": [
            ("Art.10", "ICT-related incident detection"),
        ],
        "SOC2": [
            ("CC7.2", "system monitoring includes alert tuning"),
        ],
    },
    "compliance": {
        # Compliance-category risks are framework-specific by definition,
        # so they're handled inline rather than via this map.
    },
}


def impacts_for(
    category: str,
    available_frameworks: dict[str, dict[str, str]],
    only_unmet: bool = False,
) -> list["FrameworkImpact"]:
    """Return the list of framework impacts for an insight category.

    Args:
        category: the insight category (visibility, segmentation, ...).
        available_frameworks: bundle.framework_coverage — used to filter
            so we only mention frameworks/controls actually evaluated
            for this tenant.
        only_unmet: if True (typical for risks), drop controls already
            marked `met` so the report highlights the ones a fix would
            actually move.
    """

    out: list[FrameworkImpact] = []
    cat_map = CATEGORY_IMPACT.get(category, {})

    for fw, ctrl_pairs in cat_map.items():
        present = available_frameworks.get(fw)
        if present is None:
            continue

        controls: list[tuple[str, str]] = []
        for ctrl_id, why in ctrl_pairs:
            status = present.get(ctrl_id)
            if status is None:
                continue
            if only_unmet and status.lower() == "met":
                continue
            controls.append((ctrl_id, why))

        if controls:
            out.append(FrameworkImpact(framework=fw, controls=controls))

    return out


# ---------------------------------------------------------------------------
# Lightweight value type used by Risk and Win.
# Defined here (after the function) to keep the public API tight; renderers
# import via insights.__init__.
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field


@dataclass
class FrameworkImpact:
    framework: str
    controls: list[tuple[str, str]] = field(default_factory=list)

    @property
    def control_ids(self) -> list[str]:
        return [c for c, _ in self.controls]

    def summary(self) -> str:
        """One-line summary suitable for a table cell."""
        n = len(self.controls)
        return f"{self.framework} ({n})" if n else self.framework
