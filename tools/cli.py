"""csw-insights command-line entry point.

Subcommands:
  render   - render flavor reports from an existing evidence bundle
  compare  - render a side-by-side comparison of two tenants
  collect  - (stub) drive the upstream collector against a live tenant

`render` and `compare` work today against bundles on disk. `collect` will
shell out to the upstream CSW-API-Compliance-Automation runner once it is
checked out next to this repo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from insights import (
    EvidenceBundle,
    action_plan,
    load_bundle,
    score_posture,
    top_risks,
    top_wins,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


@click.group()
def main() -> None:
    """CSW tenant insights — produce CISO and POV flavor reports."""


@main.command()
@click.option("--bundle", "bundle_path", required=True, type=click.Path(exists=True))
@click.option(
    "--flavor",
    "flavors",
    multiple=True,
    type=click.Choice(["ciso", "pov"]),
    default=("ciso", "pov"),
    help="Which flavor(s) to render.",
)
@click.option(
    "--out",
    "out_dir",
    default=None,
    type=click.Path(),
    help="Output directory (default: out/<tenant>/).",
)
def render(bundle_path: str, flavors: tuple[str, ...], out_dir: str | None) -> None:
    """Render flavor reports from an evidence bundle."""

    bundle = load_bundle(bundle_path)
    target = Path(out_dir) if out_dir else REPO_ROOT / "out" / bundle.tenant

    written: list[Path] = []
    if "ciso" in flavors:
        from flavors.ciso import render_ciso_report

        written.append(render_ciso_report(bundle, target))
    if "pov" in flavors:
        from flavors.pov import render_pov_report

        written.append(render_pov_report(bundle, target))

    for p in written:
        click.echo(f"wrote {p.relative_to(REPO_ROOT)}")


@main.command()
@click.option("--baseline", required=True, type=click.Path(exists=True))
@click.option("--candidate", required=True, type=click.Path(exists=True))
@click.option(
    "--out",
    "out_path",
    default=None,
    type=click.Path(),
    help="Output Markdown file (default: out/compare-<a>-vs-<b>.md).",
)
def compare(baseline: str, candidate: str, out_path: str | None) -> None:
    """Side-by-side comparison of two evidence bundles."""

    a = load_bundle(baseline)
    b = load_bundle(candidate)

    target = (
        Path(out_path)
        if out_path
        else REPO_ROOT / "out" / f"compare-{a.tenant}-vs-{b.tenant}.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)

    sa = score_posture(a)
    sb = score_posture(b)

    rows = [
        ("Posture score", f"{sa.total} ({sa.grade})", f"{sb.total} ({sb.grade})"),
        ("Workloads total", f"{a.workloads_total:,}", f"{b.workloads_total:,}"),
        (
            "Agent coverage",
            f"{a.agent_coverage_pct:.1f}%",
            f"{b.agent_coverage_pct:.1f}%",
        ),
        ("Scopes", f"{a.scopes_total:,}", f"{b.scopes_total:,}"),
        ("Policies", f"{a.policies_total:,}", f"{b.policies_total:,}"),
        (
            "Enforcement",
            f"{a.enforcement_pct:.0f}%",
            f"{b.enforcement_pct:.0f}%",
        ),
        ("Absolute policies", f"{a.policies_absolute:,}", f"{b.policies_absolute:,}"),
        (
            "Critical CVEs",
            f"{a.vulnerabilities_critical:,}",
            f"{b.vulnerabilities_critical:,}",
        ),
        (
            "High CVEs",
            f"{a.vulnerabilities_high:,}",
            f"{b.vulnerabilities_high:,}",
        ),
        (
            "Alerts (24h)",
            f"{a.enforcement_alerts_24h:,}",
            f"{b.enforcement_alerts_24h:,}",
        ),
    ]

    lines: list[str] = []
    lines.append(f"# Tenant comparison: {a.tenant} vs {b.tenant}\n")
    lines.append(
        f"*{a.tenant} bundle: {a.generated_at}; "
        f"{b.tenant} bundle: {b.generated_at}.*\n"
    )
    lines.append(f"| Metric | {a.tenant} | {b.tenant} |")
    lines.append("|---|---:|---:|")
    for name, va, vb in rows:
        lines.append(f"| {name} | {va} | {vb} |")
    lines.append("")
    lines.append("## Score component breakdown\n")
    lines.append(f"| Component | {a.tenant} | {b.tenant} |")
    lines.append("|---|---:|---:|")
    for k in sa.components:
        lines.append(f"| {k.title()} | {sa.components[k]} | {sb.components.get(k, 0)} |")

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    click.echo(f"wrote {target.relative_to(REPO_ROOT)}")


@main.command()
@click.option("--tenant", required=True)
def collect(tenant: str) -> None:
    """(Stub) Drive the upstream collector against a live tenant.

    This will shell out to ../upstream/CSW-API-Compliance-Automation/tools/
    once that fork is checked out alongside this repo. Today it prints the
    expected invocation so the operator can run it manually.
    """

    cfg_path = REPO_ROOT / "tenants" / tenant / "config.yaml"
    if not cfg_path.is_file():
        click.echo(f"No tenant config at {cfg_path}", err=True)
        sys.exit(2)

    import yaml

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    click.echo(
        f"Live collection for {cfg['display_name']} is not yet wired "
        f"into this CLI. Run the upstream collector manually:\n\n"
        f"    cd ../upstream/CSW-API-Compliance-Automation\n"
        f"    python -m tools.evidence_bundle "
        f"--tenant {tenant} "
        f"--cluster {cfg['cluster_url']} "
        f"--out ../../CSW-Tenant-Insights/tenants/{tenant}/evidence/\n\n"
        f"Then render with:\n\n"
        f"    csw-insights render --bundle "
        f"tenants/{tenant}/evidence/<latest>.json"
    )


if __name__ == "__main__":
    main()
