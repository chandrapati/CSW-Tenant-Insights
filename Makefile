# CSW Tenant Insights — common tasks (run from repo root)
#
#   make install   — create .venv and install package
#   make doctor    — check prerequisites
#   make demo      — render Markdown reports from synthetic data
#   make export    — demo + HTML/DOCX/PDF (needs pandoc + LibreOffice)
#   make clean     — remove generated out/ and .venv

PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin
CSW := $(BIN)/csw-insights

.PHONY: install doctor demo export clean help

help:
	@echo "CSW Tenant Insights"
	@echo ""
	@echo "  make install   Create venv and pip install -e ."
	@echo "  make doctor    Check Python, bundles, pandoc, LibreOffice"
	@echo "  make demo      Render sample CISO + POV Markdown (no API keys)"
	@echo "  make export    demo + convert to HTML/DOCX/PDF under out/"
	@echo "  make clean     Remove out/ and .venv"
	@echo ""
	@echo "No make?  ./scripts/demo.sh"

install: $(CSW)

$(CSW): pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -q --upgrade pip
	$(BIN)/pip install -q -e .
	@echo "Installed. Activate:  source $(VENV)/bin/activate"

doctor: $(CSW)
	$(CSW) doctor

demo: $(CSW)
	$(CSW) demo

export: $(CSW)
	$(CSW) demo
	@mkdir -p out/export/acme out/export/customer1 out/export
	$(BIN)/python tools/build_reports.py out/acme/*.md --out out/export/acme
	$(BIN)/python tools/build_reports.py out/customer1/*.md --out out/export/customer1
	@if [ -f out/compare-acme-vs-customer1.md ]; then \
		$(BIN)/python tools/build_reports.py out/compare-acme-vs-customer1.md --out out/export; \
	fi
	@echo "Exported under out/export/"

clean:
	rm -rf out .venv
	@echo "Removed out/ and .venv"
