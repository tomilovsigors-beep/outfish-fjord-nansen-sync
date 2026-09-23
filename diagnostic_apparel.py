import json,time
from config import settings
from supplier_client import FjordNansenClient
from importer import parse_product
TARGETS=[["ss12486","https://b2b.fjordnansen.com/product-eng-50985-STAVOY-2-0-1-C-2150g-sleeping-bag.html"],["ss2026","https://b2b.fjordnansen.com/product-eng-23021-FREDVANG-XL-sleeping-bag-12-C-740g.html"]]
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status()
  row=parse_product(r.text,r.url)
  print("SBAG "+sku+" "+json.dumps({"stock":row.get("supplier_stock"),"availability":row.get("availability"),"attrs":row.get("attributes_json")},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
