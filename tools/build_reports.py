"""Convert rendered Markdown reports into HTML / DOCX / PDF.

Pipeline (the lessons-learned version from CSW-Compliance-Mapping):

  Markdown
    | pandoc                                -> .html (self-contained, embedded CSS)
    | pandoc                                -> .docx (pandoc's OOXML)
    | LibreOffice round-trip (docx->docx)   -> .docx (Word-compatible)
    | LibreOffice                           -> .pdf

The LibreOffice round-trip is the fix for the "Word experienced an error
trying to open the file" complaint we hit on Mac/Windows. xattrs are
stripped after each render so corporate Word/Office policies don't put the
files into protected view.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STYLE_CSS = REPO_ROOT / ".build-tools" / "style.css"


def _which(name: str, fallback: str | None = None) -> str:
    """Locate an external tool; allow override for non-PATH installs."""
    found = shutil.which(name)
    if found:
        return found
    if fallback and Path(fallback).is_file():
        return fallback
    raise RuntimeError(f"{name} not found on PATH (fallback: {fallback})")


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a subprocess, surfacing stdout/stderr if it fails."""
    result = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def _strip_xattrs(path: Path) -> None:
    """Strip macOS extended attributes to keep Office out of Protected View."""
    if sys.platform != "darwin":
        return
    subprocess.run(["xattr", "-c", str(path)], check=False)
    path.chmod(0o644)


def md_to_html(md_path: Path, out_path: Path, pandoc: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            pandoc,
            "--from=gfm",
            "--to=html5",
            "--standalone",
            "--embed-resources",
            f"--include-in-header={STYLE_CSS.with_suffix('.html')}",
            "--metadata", f"title={md_path.stem}",
            "-o", str(out_path),
            str(md_path),
        ]
    )
    _strip_xattrs(out_path)


def _ensure_style_header() -> Path:
    """Pandoc's --include-in-header expects an HTML fragment, not raw CSS."""
    header = STYLE_CSS.with_suffix(".html")
    css = STYLE_CSS.read_text(encoding="utf-8")
    header.write_text(f"<style>\n{css}\n</style>\n", encoding="utf-8")
    return header


def md_to_docx(
    md_path: Path,
    out_path: Path,
    pandoc: str,
    soffice: str,
    work_dir: Path,
) -> None:
    """Markdown -> pandoc DOCX -> LibreOffice round-trip for Word compat."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    pandoc_docx = work_dir / f"{md_path.stem}.pandoc.docx"
    _run(
        [
            pandoc,
            "--from=gfm",
            "--to=docx",
            "--standalone",
            "-o", str(pandoc_docx),
            str(md_path),
        ]
    )
    # LibreOffice round-trip: re-serialize so Word/Office for Mac+Win opens cleanly
    _run(
        [
            soffice,
            "--headless",
            "--convert-to", "docx",
            "--outdir", str(work_dir),
            str(pandoc_docx),
        ]
    )
    # LibreOffice keeps the input filename, so the round-tripped file is named
    # exactly the same as the input — copy it to the desired output location.
    soffice_out = work_dir / pandoc_docx.name
    shutil.copy2(soffice_out, out_path)
    _strip_xattrs(out_path)


def docx_to_pdf(docx_path: Path, out_dir: Path, soffice: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    _run(
        [
            soffice,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(docx_path),
        ]
    )
    pdf_path = out_dir / docx_path.with_suffix(".pdf").name
    _strip_xattrs(pdf_path)
    return pdf_path


def render_md(md_path: Path, out_dir: Path, pandoc: str, soffice: str) -> dict[str, Path]:
    """Render a single Markdown file to HTML + DOCX + PDF. Returns a {ext: path} map."""
    base = md_path.stem
    work_dir = out_dir / "_work"
    written: dict[str, Path] = {}

    written["html"] = out_dir / f"{base}.html"
    md_to_html(md_path, written["html"], pandoc)

    written["docx"] = out_dir / f"{base}.docx"
    md_to_docx(md_path, written["docx"], pandoc, soffice, work_dir)

    written["pdf"] = docx_to_pdf(written["docx"], out_dir, soffice)

    shutil.rmtree(work_dir, ignore_errors=True)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs", nargs="+", type=Path, help="Markdown files to render."
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="Output directory."
    )
    args = parser.parse_args()

    pandoc = _which("pandoc")
    soffice = _which(
        "soffice",
        fallback="/Applications/LibreOffice.app/Contents/MacOS/soffice",
    )
    _ensure_style_header()

    for md in args.inputs:
        if not md.is_file():
            print(f"skip (not found): {md}", file=sys.stderr)
            continue
        produced = render_md(md, args.out.resolve(), pandoc, soffice)
        for ext, path in produced.items():
            try:
                rel = path.resolve().relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            print(f"{ext:>4}  {rel}")


if __name__ == "__main__":
    main()
