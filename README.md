# CSW Tenant Insights

CISO and POV report flavors driven from live Cisco Secure Workload tenant
evidence. This repo turns the catalogs and runbooks in our other repos into
something a customer leadership team will actually read.

## Where this fits

Three repositories, three jobs:

| Repo | What it answers | Audience |
|---|---|---|
| [`CSW-Compliance-Mapping`](https://github.com/chandrapati/CSW-Compliance-Mapping) | "How does Cisco Secure Workload map to framework X?" — narrative reports + technical runbooks for 11 frameworks. | Customers in due diligence, auditors, security teams. |
| [`CSW-API-Compliance-Automation`](https://github.com/chandrapati/CSW-API-Compliance-Automation) (fork of `jgmitter-cisco/...`) | "What does this tenant *actually* look like?" — YAML control catalogs + collectors that pull live evidence. | Internal compliance / SE. |
| **`CSW-Tenant-Insights`** *(this repo)* | "What should the CISO and the POV team *do* with that evidence?" — posture score, top-N risks/wins, 30-day plan, in two purpose-built flavors. | CISOs, boards, Cisco SE pre-sales motions. |

The split keeps the public framework documentation independent of any
specific tenant data, while letting us layer customer-specific narratives
on top without polluting the upstream catalog repo.

## The two flavors

### CISO flavor — `CSW-Posture-Brief-<tenant>.md`

A one-page board update. Posture score, top wins, top risks, a four-week
plan, and a compact compliance posture table. Designed to drop into a
monthly steering pack.

### POV flavor — `CSW-POV-Findings-<tenant>.md`

A 3–5 page talk-track for the SE leading a proof-of-value readout.
Denser numbers, demo-able artefacts called out by name, explicit
"what we'd like to do next" close.

Both flavors consume the **same evidence bundle** — they differ only in
emphasis, length, and call to action. That guarantees the CISO and the
SE are talking about the same reality.

## Quick start (synthetic data, no live tenant required)

```bash
git clone https://github.com/chandrapati/CSW-Tenant-Insights.git
cd CSW-Tenant-Insights
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Render both flavors against the synthetic ACME bundle
csw-insights render --bundle examples/acme-2026-05-01.json

# Same for the customer 1 placeholder bundle
csw-insights render --bundle examples/customer1-2026-05-01.json

# Side-by-side comparison
csw-insights compare \
  --baseline examples/acme-2026-05-01.json \
  --candidate examples/customer1-2026-05-01.json
```

Output lands in `out/<tenant>/`. Convert to DOCX/PDF/HTML with the same
pandoc pipeline used in `CSW-Compliance-Mapping`.

## Naming convention for tenants

Tenants under version control use **generic identifiers** (`customer1`,
`customer2`, …), never the customer's real name. The mapping from
identifier to real customer lives only in your local
`~/.csw/tenants.yaml` credential file. This keeps the repo safe to share
with internal collaborators and resilient to accidental
screenshot/transcript leaks.

## Live tenant run

1. **Check out the upstream automation alongside this repo.**

   ```bash
   cd ..
   git clone https://github.com/chandrapati/CSW-API-Compliance-Automation upstream/CSW-API-Compliance-Automation
   ```

2. **Add tenant credentials in your local credential store** (never in this repo).

   ```yaml
   # ~/.csw/tenants.yaml
   acme:
     api_key:    "…"
     api_secret: "…"
   customer1:
     api_key:    "…"
     api_secret: "…"
   ```

3. **Run the collector** (from upstream) against the tenant, dropping the
   evidence bundle into this repo's `tenants/<id>/evidence/` directory.

4. **Render** with `csw-insights render --bundle tenants/<id>/evidence/<file>.json`.

5. **Compare** runs over time (or across tenants) with `csw-insights compare`.

## Repo layout

```
CSW-Tenant-Insights/
├── insights/             shared analytics (posture, risks, wins, actions)
├── flavors/
│   ├── ciso/             one-page board brief renderer + template
│   └── pov/              SE talk-track renderer + template
├── tenants/
│   ├── _template/        copy this to add a new tenant
│   ├── acme/             synthetic demo tenant
│   └── customer1/        live pilot configuration (real customer name lives only in your local creds)
├── tools/
│   └── cli.py            csw-insights entry point
└── examples/             synthetic evidence bundles for demos
```

## Contributing changes back upstream

The catalogs in `CSW-API-Compliance-Automation` are the source of truth
for what gets evaluated. If a renderer here surfaces a control or
metric the upstream catalog doesn't cover, the right move is a PR to
the upstream catalog YAML — not a local extension here. Keep this repo
focused on *narrative* and *insight*, not *catalog content*.

## Status

- [x] Insights layer + both flavor renderers
- [x] Synthetic demo bundles for ACME and customer 1
- [x] CLI: `render`, `compare`
- [ ] Live `collect` wired to upstream evidence_bundle.py
- [ ] DOCX / PDF / HTML pipeline integrated (use the build-html.py from CSW-Compliance-Mapping)
- [ ] Trend reporting across multiple bundles per tenant
