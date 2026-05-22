# CSW Tenant Insights

CISO and POV report flavors driven from Cisco Secure Workload tenant evidence — posture score, top risks/wins, and a 30-day plan in two purpose-built formats.

**Users get stuck on “how do I run this?”** — use the table below. Full steps and troubleshooting: **[docs/RUNBOOK.md](docs/RUNBOOK.md)**.

## How to run this (pick one)

| I want to… | Command | Time |
|---|---|---|
| **See finished reports** (no install) | Open [`examples/sample-reports/`](./examples/sample-reports/) (PDF / HTML / DOCX) | 1 min |
| **Try the tool** (synthetic data, no API keys) | `make demo` or `./scripts/demo.sh` | 2 min |
| **Check my laptop is ready** | `make install && make doctor` | 3 min |
| **Build PDF/DOCX/HTML** from Markdown | `make export` (needs [pandoc](https://pandoc.org) + [LibreOffice](https://www.libreoffice.org)) | 5 min |
| **Use a live CSW tenant** | [docs/RUNBOOK.md § Live tenant](docs/RUNBOOK.md#live-tenant-workflow) | 30+ min |

### Copy-paste: first run (Markdown only)

```bash
git clone https://github.com/chandrapati/CSW-Tenant-Insights.git
cd CSW-Tenant-Insights
make install
source .venv/bin/activate   # Windows: .venv\Scripts\activate
csw-insights doctor
csw-insights demo
ls out/acme out/customer1
```

You should see `CSW-Posture-Brief-*.md` and `CSW-POV-Findings-*.md` under `out/`. If `doctor` shows red **FAIL** lines, fix those before continuing — see [Troubleshooting](docs/RUNBOOK.md#troubleshooting).

### CLI commands

| Command | Purpose |
|---|---|
| `csw-insights doctor` | Verify Python, install, sample bundles, optional PDF tools |
| `csw-insights demo` | Render ACME + customer1 + comparison (no live tenant) |
| `csw-insights render --bundle <file.json>` | Render CISO and/or POV Markdown from one bundle |
| `csw-insights compare --baseline … --candidate …` | Side-by-side tenant comparison |
| `csw-insights export --from-demo --out out/export` | HTML/DOCX/PDF (after `demo`) |
| `csw-insights collect --tenant <id>` | Print live-collection steps (collector is upstream) |

---

## Sample reports (no install)

Pre-rendered outputs from synthetic **ACME** (mature, 75/C) and **customer1** (early, 29/F):

| Tenant | CISO brief | POV findings |
|---|---|---|
| ACME | [PDF](./examples/sample-reports/acme/CSW-Posture-Brief-acme.pdf) · [HTML](./examples/sample-reports/acme/CSW-Posture-Brief-acme.html) | [PDF](./examples/sample-reports/acme/CSW-POV-Findings-acme.pdf) · [HTML](./examples/sample-reports/acme/CSW-POV-Findings-acme.html) |
| Customer 1 | [PDF](./examples/sample-reports/customer1/CSW-Posture-Brief-customer1.pdf) · [HTML](./examples/sample-reports/customer1/CSW-Posture-Brief-customer1.html) | [PDF](./examples/sample-reports/customer1/CSW-POV-Findings-customer1.pdf) · [HTML](./examples/sample-reports/customer1/CSW-POV-Findings-customer1.html) |
| Compare | [PDF](./examples/sample-reports/compare-acme-vs-customer1.pdf) · [HTML](./examples/sample-reports/compare-acme-vs-customer1.html) | — |

DOCX variants are in the same folders. Use **PDF** for readouts, **HTML** for email/chat links, **DOCX** if you need to edit before sharing.

---

## Where this fits in the CSW repo family

| Repo | Job |
|---|---|
| [CSW-Compliance-Mapping](https://github.com/chandrapati/CSW-Compliance-Mapping) | How CSW maps to framework X (HIPAA, PCI, NIST, …) |
| [CSW-API-Compliance-Automation](https://github.com/chandrapati/CSW-API-Compliance-Automation) | Live tenant evidence collection + control catalogs |
| **[CSW-Tenant-Insights](https://github.com/chandrapati/CSW-Tenant-Insights)** *(here)* | CISO + POV narratives from that evidence |
| [CSW-User-Education](https://github.com/chandrapati/CSW-User-Education) | Learning path, POV runbook, video catalog |

---

## The two report flavors

Both consume the **same evidence bundle**; only tone and length differ.

- **CISO** — `CSW-Posture-Brief-<tenant>.md` — one-page board update (score, wins, risks, 30-day plan).
- **POV** — `CSW-POV-Findings-<tenant>.md` — 3–5 page SE readout with demo artefacts and next steps.

---

## Repo layout

```
CSW-Tenant-Insights/
├── Makefile              make install | demo | export | doctor
├── scripts/demo.sh       same as make demo, without Make
├── docs/RUNBOOK.md       full operator guide + troubleshooting
├── insights/             shared analytics (posture, risks, wins)
├── flavors/ciso|pov/     Jinja templates + renderers
├── tools/
│   ├── cli.py            csw-insights entry point
│   └── build_reports.py  Markdown → HTML / DOCX / PDF
├── examples/*.json       synthetic bundles (safe to commit)
├── examples/sample-reports/   pre-built showcase artefacts
└── tenants/_template/    copy to add a live tenant config
```

Generated locally (not committed): `out/`, `tenants/*/evidence/`, `.venv/`.

---

## Tenant naming and credentials

- Repo uses generic IDs (`customer1`, `customer2`, …), never real customer names.
- API keys live only in `~/.csw/tenants.yaml` (or your secrets manager).
- `tenants/<id>/config.yaml` references credentials by `credentials_ref` only.

---

## Contributing upstream

Control definitions belong in **CSW-API-Compliance-Automation**, not here. This repo stays focused on narrative and insight; open catalog PRs upstream when a metric is missing.

---

## Status

- [x] `csw-insights` CLI: `doctor`, `demo`, `render`, `compare`, `export`, `collect` (instructions)
- [x] Makefile + `scripts/demo.sh` for one-command demo
- [x] [docs/RUNBOOK.md](docs/RUNBOOK.md) operator guide
- [x] Synthetic bundles + pre-rendered samples
- [ ] Live `collect` wired to upstream collector
- [ ] Trend reporting across bundles per tenant
- [ ] GitHub Pages for HTML samples
