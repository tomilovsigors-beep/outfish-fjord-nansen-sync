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


## Pipeline ownership marker

Do not decide mass-update ownership from product creation date.

A Shopify product is Fjord-pipeline-managed only when it carries the explicit internal ownership marker:

- namespace: outfish
- key: fjord_managed
- value: true

Only products created by the Fjord pipeline may receive this marker.

A product without this marker is treated as manually/external managed, even if it was created after the Fjord integration was enabled.

Rules:
- manually created products never receive automatic content, SEO, price, collection, tag, image, translation, handle, or publication-status updates;
- if a manually managed product is explicitly matched to a supplier item, inventory/availability sync remains allowed;
- newly created Fjord pipeline products receive the marker at creation time and start as DRAFT;
- removing or disabling the marker must immediately exclude that product from future mass content/price updates.
