.PHONY: dev ingest digest sample-data setup-cron test-scraper

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

ingest:
	python -m cli ingest

digest:
	python -m cli digest

alert:
	python -m cli alert

sample-data:
	python -m cli sample-data

setup-cron:
	./scripts/setup_cron.sh

test-scraper:
	@echo "Testing scraper with real TTU website..."
	python -m cli ingest
