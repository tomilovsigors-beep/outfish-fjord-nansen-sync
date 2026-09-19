# Shopify content preservation policy

Existing Shopify products are content-protected.

A row is treated as an existing Shopify product when shopify_product_id is present.

For existing products, the Fjord supplier pipeline MUST NOT overwrite:
- title
- description / descriptionHtml
- SEO title
- SEO description
- handle
- product type
- collections
- tags
- images / media
- translations
- publication status

Supplier synchronization for existing products may only update fields explicitly enabled for operational sync, such as:
- supplier stock / availability
- approved price fields
- supplier source metadata

New products without shopify_product_id may receive generated EN/LV/RU content and planned category/collection assignments before being created as DRAFT.

Manual content always wins.


## Manual/existing product protection

Products that already existed in Shopify before Fjord sync adoption, or were created/maintained manually, are excluded from mass content and price updates.

For those protected existing products:
- automatic supplier sync may update inventory/availability only;
- title, descriptions, SEO, handle, product type, collections, tags, images, translations, publication status, price, and compare-at price remain untouched;
- content generation jobs must skip them entirely.

For products newly created by the Fjord pipeline:
- create as DRAFT only;
- after creation, inventory/availability may sync automatically;
- future content changes require an explicit approved content workflow, never a blanket overwrite;
- price may only follow the dedicated new-product pricing rule unless later changed manually, after which the manual value wins.
