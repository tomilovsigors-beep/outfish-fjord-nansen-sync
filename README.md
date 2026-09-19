# Outfish Fjord Nansen Supplier Sync

Standalone Fjord Nansen B2B → Supplier Master → Shopify integration.

This repository is intentionally independent from LOWA, 220.lv feeds, Salidzini and Kurpirkt projects.

## Flow

Fjord Nansen B2B
→ normalized supplier data
→ Fjord Nansen Supplier Master (Google Sheets)
→ Shopify Outfish
→ existing marketplace flows consume Shopify data downstream.

## Runtime migration

Fjord B2B fetching is being migrated from Render to GitHub Actions because Render connections to the supplier started timing out.

Current GitHub Actions stage is intentionally manual and parse-only:

- workflow: `.github/workflows/fjord-parse.yml`
- trigger: manual `workflow_dispatch`
- `DRY_RUN=true`
- `SHEET_WRITE_ENABLED=false`
- `SHOPIFY_WRITE_ENABLED=false`
- parsed rows are uploaded as a 7-day artifact named `fjord-parse-output`

After one clean full-catalog run, daily scheduling and Google Sheets writes can be enabled.

## GitHub Actions secrets

Repository → Settings → Secrets and variables → Actions → New repository secret.

Required now:

- `FJORD_B2B_LOGIN`
- `FJORD_B2B_PASSWORD`

Required later for automatic FN_RAW writes:

- `GOOGLE_SERVICE_ACCOUNT_JSON`

Do not commit credential values to this repository.

## Safety model

- No supplier credentials are committed to GitHub.
- Initial mode is `DRY_RUN=true`.
- Shopify writes are disabled by default.
- EAN/GTIN is never fabricated.
- If supplier SKU is missing, importer creates a deterministic internal SKU with `FN-AUTO-` prefix.
- Existing Outfish physical stock has priority over supplier stock.
- Manual price/content/image overrides must not be overwritten by supplier refresh.

## Supplier Master

Google Sheet ID:
`1RRsV9mHZMV3gfQGIJq1OGQgc0qyI4zqJ-yv9Fg9Ygl8`

Published Shopify locales:

- EN (primary)
- LV
- RU

## Render

Render is no longer the preferred network path for Fjord B2B fetching. Keep its Fjord task in safe mode until GitHub Actions is validated:

- `DRY_RUN=true`
- `SHEET_WRITE_ENABLED=false`
- `SHOPIFY_WRITE_ENABLED=false`

## Current stage

Manual GitHub Actions parse-only validation. No Shopify mutation is enabled.
