# ICE Contracts

## Canonical input

```csv
input_id,main_text,country_code,ean,retailer_name,PG_name
```

Required after normalization:

- `input_id`
- `main_text`
- `country_code`
- `PG_name`

## Search adapter contract

ICE maps each canonical row to `web_search_tool`'s `ProductQuery`.

Expected fields used by ICE:

- `input_id` / `row_id`
- `product_url`
- `verified_exact_url`
- `best_available_url`
- `best_reference_url`
- `confidence`
- `needs_review`
- `url_decision_status`
- `selection_scope`
- `final_justification`

## Scrape adapter contract

ICE maps the selected URL candidate to `product_scrape_tool`'s `ScrapeRequest` / batch input.

Fields emitted in `scrape/scrape_input.csv`:

- `input_id`
- `product_url`
- `main_text`
- `country_code`
- `ean`
- `retailer_name`
- `requested_retailer_name`
- `requested_country_code`
- `source_url_role`
- `upstream_ai_evidence`
- `candidate_snippets`
- `search_evidence`

## Artifact routing contract

ICE reads scraper batch output and routes each row to one of:

- `CODING_READY`
- `CODING_READY_WITH_REVIEW`
- `REPAIR_REQUIRED`
- `REVIEW_REQUIRED`
- `DO_NOT_CODE`

## Coding adapter contract

ICE builds `product_batch_input_canonical_pg_names.csv` for `product_coding_tool`.

Minimum fields:

- `input_id`
- `PG_name`

Additional context fields are preserved for audit.
