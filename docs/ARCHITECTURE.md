# ICE Architecture

ICE is a non-linear orchestration layer over three specialist tools.

## Specialist boundaries

| Tool | Boundary |
|---|---|
| `web_search_tool` | Discovers URL candidates and evidence; does not build the final product artifact |
| `product_scrape_tool` | Scrapes known URLs; does not search |
| `product_coding_tool` | Codes features from scraped artifacts and PG rules; does not search or scrape |

## Non-linear graph

```text
                         ┌──────────────────────┐
                         │ Canonical input CSV  │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
              ▼                                           ▼
   ┌──────────────────────┐                    ┌──────────────────────┐
   │ PG feature prepare   │                    │ URL discovery        │
   │ product_coding_tool  │                    │ web_search_tool      │
   └──────────┬───────────┘                    └──────────┬───────────┘
              │                                           │
              │                                           ▼
              │                              ┌────────────────────────┐
              │                              │ Candidate URL routing  │
              │                              └──────────┬─────────────┘
              │                                         ▼
              │                              ┌────────────────────────┐
              │                              │ Full product scraping  │
              │                              │ product_scrape_tool    │
              │                              └──────────┬─────────────┘
              │                                         ▼
              │                              ┌────────────────────────┐
              │                              │ Artifact quality gate  │
              │                              └─────┬──────────┬───────┘
              │                                    │          │
              │                              ready │          │ repair/review
              │                                    ▼          ▼
              │                         ┌───────────────┐  repair loop
              └────────────────────────▶│ product code  │      │
                                        │ product_coding│◀─────┘
                                        └───────┬───────┘
                                                ▼
                                      ┌──────────────────────┐
                                      │ final coded output   │
                                      └──────────────────────┘
```

## Decision types

### Candidate fan-out
When search confidence is weak, ICE can scrape more than one candidate URL instead of forcing the first URL into coding.

### Evidence fan-in
When multiple candidate artifacts exist, ICE selects the strongest artifact based on scrape quality, source alignment, and product identity signals.

### Repair loop
If a scrape is blocked or weak, ICE can go back to URL discovery or retry scraping with a different candidate. If coding fails only for a few features, ICE retries only those features through the coding tool's fallback path.

### Review queue
When identity or evidence cannot be proven, ICE stops safely and sends the row to review rather than creating misleading automated codes.

## Execution modes

| Mode | Behavior |
|---|---|
| `poc_fast` | top candidate only, minimal repair |
| `manager_validation` | top 2 candidates when uncertain, one repair attempt, strong audit outputs |
| `production_audit` | broader candidate fan-out, strict quality gates, full repair/review reporting |
