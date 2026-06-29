# ICE — Integrated Codebase Engine

ICE connects three specialist repositories into one **non-linear product coding harness**:

| Specialist repo | Responsibility in ICE |
|---|---|
| [`web_search_tool`](https://github.com/Akilankm/web_search_tool) | Product URL discovery, candidate evidence, URL confidence, SerpAPI AI Mode validation |
| [`product_scrape_tool`](https://github.com/Akilankm/product_scrape_tool) | Known URL → product-only scrape artifact using Crawl4AI |
| [`product_coding_tool`](https://github.com/Akilankm/product_coding_tool) | Scraped artifact + PG feature rules → coded feature CSV |

ICE is **not** a simple `search → scrape → code` script. It is a controller-driven evidence graph with candidate fan-out, artifact-quality gates, repair routing, and review queues.

```text
input CSV
  ├── PG feature preparation
  └── URL discovery
          ├── exact retailer candidate
          ├── same-country fallback
          └── global fallback
                ↓
        candidate selection
                ↓
        full product scraping
                ↓
        artifact quality routing
          ├── coding-ready
          ├── repair-required
          └── review-required
                ↓
        product feature coding
                ↓
        final integrated output
```

## Runtime input

```csv
input_id,main_text,country_code,ean,retailer_name,PG_name
ROW_0001,FIGURKA BAVYTOY TUBA SE ZVÍŘÁTKY 18 KS,CZ,,Alza,Figures/Build Sets
```

Required after normalization: `main_text`, `country_code`, `PG_name`. `input_id` is generated when missing. `ean` and `retailer_name` are optional.

## Install

```bash
pdm install
```

## Run

```bash
pdm run ice run \
  --input data/products.csv \
  --pg-feature-input data/pg_feature_coding_input.csv \
  --output-root outputs/run_001 \
  --mode manager_validation \
  --env-file .env
```

## Output

```text
outputs/run_001/
├── canonical_input.csv
├── search/url_matches.csv
├── search/review_queue.csv
├── scrape/scrape_input.csv
├── scrape/scraped/
├── routing/coding_ready_products.csv
├── routing/repair_products.csv
├── routing/review_products.csv
├── coding/product_batch_input_canonical_pg_names.csv
├── final_product_status.csv
├── integrated_metrics.json
└── integrated_run_summary.md
```

See `docs/ARCHITECTURE.md` and `docs/CONTRACTS.md` for the full design.
