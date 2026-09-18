# Outfish Fjord Nansen Supplier Sync

Standalone Fjord Nansen B2B → Supplier Master → Shopify integration.

This repository is intentionally independent from LOWA, 220.lv feeds, Salidzini and Kurpirkt projects.

## Flow

Fjord Nansen B2B
→ normalized supplier data
→ Fjord Nansen Supplier Master (Google Sheets)
→ Shopify Outfish
→ existing marketplace flows consume Shopify data downstream.

## Safety model

- Supplier credentials exist only in Render environment variables.
- No credentials are committed to GitHub.
- Initial mode is DRY_RUN=true.
- Shopify writes are disabled by default.
- EAN/GTIN is never fabricated.
- If supplier SKU is missing, importer creates a deterministic internal SKU with FN-AUTO- prefix.
- Existing Outfish physical stock has priority over supplier stock.
- Supplier data refreshes daily.
- Manual price/content/image overrides must not be overwritten by supplier refresh.

## Supplier Master

Google Sheet ID:
`1RRsV9mHZMV3gfQGIJq1OGQgc0qyI4zqJ-yv9Fg9Ygl8`

Published Shopify locales:
- EN (primary)
- LV
- RU

## Render secrets to set

Required for B2B audit:
- `FJORD_B2B_LOGIN`
- `FJORD_B2B_PASSWORD`

Already safe to configure as plain settings:
- `FJORD_B2B_BASE_URL=https://b2b.fjordnansen.com`
- `FJORD_SUPPLIER_SHEET_ID=1RRsV9mHZMV3gfQGIJq1OGQgc0qyI4zqJ-yv9Fg9Ygl8`
- `DRY_RUN=true`
- `SHOPIFY_WRITE_ENABLED=false`

Later, only when write stages are approved:
- `SHOPIFY_STORE_DOMAIN`
- `SHOPIFY_ADMIN_ACCESS_TOKEN`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

## Current stage

Bootstrap and authenticated B2B audit. No Shopify mutation is implemented yet.
