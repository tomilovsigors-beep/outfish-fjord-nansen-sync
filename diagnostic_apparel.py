import json,time
from config import settings
from supplier_client import FjordNansenClient
from importer import parse_product
TARGETS=[["ss9753","https://b2b.fjordnansen.com/product-eng-45144-NORDKAPP-500-XL-2-0-RIGHT-down-sleeping-bag-5-900-g.html"],["ss9085","https://b2b.fjordnansen.com/product-eng-43872-NORDKAPP-300-MID-LEFT-down-sleeping-bag-1-C-650-g.html"]]
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for sku,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status()
  row=parse_product(r.text,r.url)
  print("DOWNBAG "+sku+" "+json.dumps({"stock":row.get("supplier_stock"),"attrs":row.get("attributes_json")},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
