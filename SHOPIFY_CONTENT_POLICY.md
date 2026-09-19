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
