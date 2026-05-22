# CSW Tenant Insights — Runbook

Step-by-step instructions for operators who need to **run** this repo, not just read the samples.

## Choose your path

| Goal | What to run | API keys? | pandoc / LibreOffice? |
|---|---|:---:|:---:|
| See what the reports look like | Open files under [`examples/sample-reports/`](../examples/sample-reports/) | No | No |
| Generate Markdown locally (demo) | `make demo` or `./scripts/demo.sh` | No | No |
| Generate PDF / DOCX / HTML | `make export` after `make demo` | No | Yes |
| Reports from a **live** CSW tenant | § Live tenant workflow below | Yes | Optional |

---

## First-time setup (all paths except “samples only”)

From the repository root:

```bash
git clone https://github.com/chandrapati/CSW-Tenant-Insights.git
cd CSW-Tenant-Insights
make install          # creates .venv and installs csw-insights
source .venv/bin/activate
csw-insights doctor   # must show all [ok] for demo; pandoc/soffice optional until export
```

**Without Make** (Windows or minimal environments):

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
pip install -e .
csw-insights doctor
```

---

## Demo path (synthetic data — recommended first run)

No Cisco Secure Workload credentials. Uses JSON bundles in `examples/`.

```bash
csw-insights demo
```

Outputs Markdown under:

- `out/acme/` — mature tenant (posture ~75/C)
- `out/customer1/` — early tenant (posture ~29/F)
- `out/compare-acme-vs-customer1.md`

Equivalent:

```bash
make demo
# or
./scripts/demo.sh
```

### Render a single bundle manually

```bash
csw-insights render --bundle examples/acme-2026-05-01.json
csw-insights render --bundle examples/customer1-2026-05-01.json --flavor ciso
csw-insights compare \
  --baseline examples/acme-2026-05-01.json \
  --candidate examples/customer1-2026-05-01.json
```

---

## Export path (HTML / DOCX / PDF)

Requires **pandoc** and **LibreOffice** (`soffice` on PATH, or the default Mac app bundle path).

```bash
make export
```

Or after `csw-insights demo`:

```bash
python tools/build_reports.py out/acme/*.md --out out/export/acme
python tools/build_reports.py out/customer1/*.md --out out/export/customer1
```

Pre-built reference copies live in `examples/sample-reports/` (safe to open in Word without running the pipeline).

---

## Live tenant workflow

This repo **does not** call the CSW API by itself today. You collect evidence with the upstream automation repo, then **render** here.

### 1. Add a tenant directory

```bash
cp -r tenants/_template tenants/customer2
# Edit tenants/customer2/config.yaml — cluster_url, frameworks, catalogs
```

Never put API keys in `config.yaml`. Use a local credential file only.

### 2. Store credentials locally

```yaml
# ~/.csw/tenants.yaml  (never commit this file)
customer2:
  api_key: "YOUR_KEY"
  api_secret: "YOUR_SECRET"
```

The `credentials_ref` field in `config.yaml` must match the key in this file.

### 3. Clone the upstream collector (sibling directory is easiest)

```bash
cd ..
git clone https://github.com/chandrapati/CSW-API-Compliance-Automation.git
cd CSW-API-Compliance-Automation
# follow that repo's README to install and run the collector
```

### 4. Collect evidence JSON

From the upstream repo (exact flags may vary — check upstream README):

```bash
python -m tools.evidence_bundle \
  --tenant customer2 \
  --cluster https://YOUR-CSW-CLUSTER \
  --out ../CSW-Tenant-Insights/tenants/customer2/evidence/
```

Shortcut to print tailored commands for a tenant already configured here:

```bash
csw-insights collect --tenant customer2
```

### 5. Render reports

```bash
cd ../CSW-Tenant-Insights
csw-insights render --bundle tenants/customer2/evidence/<latest-bundle>.json
```

Evidence under `tenants/*/evidence/` is gitignored by design.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `csw-insights: command not found` | Activate venv: `source .venv/bin/activate`, or run `make install`. |
| `No module named 'insights'` | From repo root: `pip install -e .` |
| `doctor` fails on sample bundles | Run commands from repo root; re-clone if `examples/*.json` missing. |
| `pandoc not found` | Install pandoc; only needed for `make export`, not `make demo`. |
| `soffice not found` | Install LibreOffice; on Mac the CLI is often `/Applications/LibreOffice.app/Contents/MacOS/soffice`. |
| Word won't open DOCX | Use the LibreOffice round-trip pipeline (`build_reports.py`), not raw pandoc DOCX alone. |
| `collect` only prints instructions | Expected — live collection is upstream; this repo renders bundles on disk. |
| Empty or stale `out/` | `make clean` then `make demo` again. |

---

## What gets committed vs generated

| Path | Committed? |
|---|---|
| `examples/*.json` | Yes — synthetic bundles |
| `examples/sample-reports/` | Yes — showcase PDF/HTML/DOCX |
| `out/` | No — your local renders |
| `tenants/*/evidence/` | No — live customer data |
| `~/.csw/tenants.yaml` | Never — credentials |

---

## Related repositories

- [CSW-User-Education](https://github.com/chandrapati/CSW-User-Education) — learning path and POV runbook
- [CSW-Compliance-Mapping](https://github.com/chandrapati/CSW-Compliance-Mapping) — framework narratives
- [CSW-API-Compliance-Automation](https://github.com/chandrapati/CSW-API-Compliance-Automation) — live evidence collection
