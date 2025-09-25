**architecture.md**
```md
# Architecture
- Web (Flask): `/analysis`, buttons, busy-state **409**
- ETL: scrape → clean → load (idempotent)
- DB: Postgres via `PG_DSN`