"""CISO flavor renderer — produces the one-page board brief."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from insights import (
    EvidenceBundle,
    action_plan,
    score_posture,
    top_risks,
    top_wins,
)


def render_ciso_report(bundle: EvidenceBundle, out_dir: Path) -> Path:
    """Render the CISO brief as Markdown. Returns the path written."""

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"CSW-Posture-Brief-{bundle.tenant}.md"

    score = score_posture(bundle)
    wins = top_wins(bundle)
    risks = top_risks(bundle)
    plan = action_plan(bundle, risks)

    env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent)),
        autoescape=select_autoescape(disabled_extensions=("md", "j2"), default=False),
        keep_trailing_newline=True,
    )
    template = env.get_template("template.md.j2")
    text = template.render(b=bundle, score=score, wins=wins, risks=risks, plan=plan)
    out_path.write_text(text, encoding="utf-8")
    return out_path
