"""csw-insights command-line entry point.

Subcommands:
  doctor   - check prerequisites before you run anything
  demo     - render sample reports from bundled synthetic data (no live tenant)
  render   - render flavor reports from an evidence bundle on disk
  compare  - side-by-side comparison of two bundles
  export   - convert rendered Markdown to HTML / DOCX / PDF
  collect  - print instructions for live tenant collection (upstream collector)
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click

from insights import load_bundle, score_posture

REPO_ROOT = Path(__file__).resolve().parent.parent

ACME_BUNDLE = REPO_ROOT / "examples" / "acme-2026-05-01.json"
CUSTOMER1_BUNDLE = REPO_ROOT / "examples" / "customer1-2026-05-01.json"


def _render_bundle(
    bundle_path: Path,
    flavors: tuple[str, ...],
    out_dir: Path | None,
) -> list[Path]:
    bundle = load_bundle(bundle_path)
    target = out_dir if out_dir else REPO_ROOT / "out" / bundle.tenant
    written: list[Path] = []
    if "ciso" in flavors:
        from flavors.ciso import render_ciso_report

        written.append(render_ciso_report(bundle, target))
    if "pov" in flavors:
        from flavors.pov import render_pov_report

        written.append(render_pov_report(bundle, target))
    return written


@click.group()
@click.version_option(package_name="csw-tenant-insights", prog_name="csw-insights")
def main() -> None:
    """CSW tenant insights — CISO and POV reports from tenant evidence bundles."""


@main.command()
def doctor() -> None:
    """Check Python, package install, sample bundles, and optional PDF tools."""

    ok = True

    def check(label: str, passed: bool, detail: str = "") -> None:
        nonlocal ok
        mark = click.style("ok", fg="green") if passed else click.style("FAIL", fg="red")
        line = f"  [{mark}] {label}"
        if detail:
            line += f" — {detail}"
        click.echo(line)
        if not passed:
            ok = False

    click.echo("CSW Tenant Insights — environment check\n")
    check("Python >= 3.10", sys.version_info >= (3, 10), sys.version.split()[0])

    try:
        import insights  # noqa: F401

        check("Package import (insights)", True)
    except ImportError as exc:
        check("Package import (insights)", False, str(exc))
        check(
            "Editable install",
            False,
            "run: pip install -e .  (from repo root, venv activated)",
        )

    for label, path in (
        ("ACME sample bundle", ACME_BUNDLE),
        ("Customer1 sample bundle", CUSTOMER1_BUNDLE),
    ):
        check(label, path.is_file(), str(path.relative_to(REPO_ROOT)))

    pandoc = shutil.which("pandoc")
    check(
        "pandoc (for HTML/DOCX/PDF export)",
        pandoc is not None,
        pandoc or "install pandoc — export will fail without it",
    )

    soffice = shutil.which("soffice") or (
        "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").is_file()
        else None
    )
    check(
        "LibreOffice soffice (for DOCX/PDF export)",
        soffice is not None,
        soffice or "install LibreOffice — DOCX/PDF export will fail without it",
    )

    creds = Path.home() / ".csw" / "tenants.yaml"
    if creds.is_file():
        check("Live tenant credentials", True, str(creds))
    else:
        click.echo(
            click.style(
                f"  [ -- ] Live tenant credentials — optional ({creds} not found; "
                "only needed for real tenants, not make demo)",
                fg="yellow",
            )
        )

    click.echo("")
    if ok:
        click.echo("Ready. Run:  make demo   or   csw-insights demo")
    else:
        click.echo("Fix the FAIL items above, then re-run:  csw-insights doctor", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--flavor",
    "flavors",
    multiple=True,
    type=click.Choice(["ciso", "pov"]),
    default=("ciso", "pov"),
    help="Which flavor(s) to render.",
)
@click.option(
    "--no-compare",
    is_flag=True,
    help="Skip the ACME vs customer1 comparison report.",
)
def demo(flavors: tuple[str, ...], no_compare: bool) -> None:
    """Render sample reports from synthetic bundles (no API keys required)."""

    if not ACME_BUNDLE.is_file() or not CUSTOMER1_BUNDLE.is_file():
        click.echo(
            "Sample bundles missing under examples/. "
            "Re-clone the repo or run from the repository root.",
            err=True,
        )
        sys.exit(2)

    click.echo("Rendering synthetic demo tenants (no live CSW API calls)…\n")
    for bundle in (ACME_BUNDLE, CUSTOMER1_BUNDLE):
        for path in _render_bundle(bundle, flavors, None):
            click.echo(f"  wrote {path.relative_to(REPO_ROOT)}")

    if not no_compare:
        ctx = click.get_current_context()
        ctx.invoke(
            compare,
            baseline=str(ACME_BUNDLE),
            candidate=str(CUSTOMER1_BUNDLE),
            out_path=None,
        )

    click.echo("\nDone. Open Markdown under out/:")
    click.echo(f"  {REPO_ROOT / 'out' / 'acme'}")
    click.echo(f"  {REPO_ROOT / 'out' / 'customer1'}")
    click.echo("\nPre-built PDF/HTML samples (no install):  examples/sample-reports/")
    click.echo("For PDF/DOCX from your Markdown:  make export   or  csw-insights export …")


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

    target = Path(out_dir) if out_dir else None
    for path in _render_bundle(Path(bundle_path), flavors, target):
        click.echo(f"wrote {path.relative_to(REPO_ROOT)}")


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


@main.command("export")
@click.argument(
    "markdown_files",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--out",
    "out_dir",
    required=True,
    type=click.Path(),
    help="Directory for HTML, DOCX, and PDF output.",
)
@click.option(
    "--from-demo",
    is_flag=True,
    help="Export all Markdown produced by the last demo (out/acme, out/customer1, compare).",
)
def export_cmd(
    markdown_files: tuple[str, ...],
    out_dir: str,
    from_demo: bool,
) -> None:
    """Convert rendered Markdown to HTML, DOCX, and PDF (needs pandoc + LibreOffice)."""

    paths: list[Path] = [Path(p) for p in markdown_files]

    if from_demo:
        paths = []
        for sub in ("acme", "customer1"):
            paths.extend(sorted((REPO_ROOT / "out" / sub).glob("*.md")))
        compare_md = next(REPO_ROOT.glob("out/compare-*.md"), None)
        if compare_md:
            paths.append(compare_md)
        if not paths:
            click.echo(
                "No demo Markdown under out/. Run:  csw-insights demo  first.",
                err=True,
            )
            sys.exit(2)

    if not paths:
        click.echo(
            "Pass one or more .md files, or use --from-demo after csw-insights demo.",
            err=True,
        )
        sys.exit(2)

    from tools.build_reports import render_md, _which, _ensure_style_header

    target = Path(out_dir).resolve()
    pandoc = _which("pandoc")
    soffice = _which(
        "soffice",
        fallback="/Applications/LibreOffice.app/Contents/MacOS/soffice",
    )
    _ensure_style_header()

    for md in paths:
        produced = render_md(md.resolve(), target, pandoc, soffice)
        for ext, path in produced.items():
            try:
                rel = path.resolve().relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            click.echo(f"{ext:>4}  {rel}")


@main.command()
@click.option("--tenant", required=True)
def collect(tenant: str) -> None:
    """Print how to collect live evidence (upstream collector — not wired in yet)."""

    cfg_path = REPO_ROOT / "tenants" / tenant / "config.yaml"
    if not cfg_path.is_file():
        click.echo(
            f"No tenant config at {cfg_path.relative_to(REPO_ROOT)}\n\n"
            f"Copy tenants/_template/ to tenants/{tenant}/ and edit config.yaml.\n"
            "See docs/RUNBOOK.md § Live tenant workflow.",
            err=True,
        )
        sys.exit(2)

    import yaml

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    creds = Path.home() / ".csw" / "tenants.yaml"
    click.echo(
        f"Live collection is not automated in csw-insights yet.\n\n"
        f"Tenant: {cfg.get('display_name', tenant)} ({cfg['cluster_url']})\n"
        f"Credentials: {creds}  (key: {cfg.get('credentials_ref', tenant)})\n\n"
        f"1. Clone upstream collector (once):\n"
        f"     git clone https://github.com/chandrapati/CSW-API-Compliance-Automation \\\n"
        f"       ../CSW-API-Compliance-Automation\n\n"
        f"2. Run collector (from upstream repo):\n"
        f"     cd ../CSW-API-Compliance-Automation\n"
        f"     python -m tools.evidence_bundle --tenant {tenant} \\\n"
        f"       --cluster {cfg['cluster_url']} \\\n"
        f"       --out {REPO_ROOT / 'tenants' / tenant / 'evidence'}\n\n"
        f"3. Render reports:\n"
        f"     cd {REPO_ROOT}\n"
        f"     csw-insights render --bundle tenants/{tenant}/evidence/<file>.json\n\n"
        f"Full steps: docs/RUNBOOK.md"
    )


if __name__ == "__main__":
    main()
