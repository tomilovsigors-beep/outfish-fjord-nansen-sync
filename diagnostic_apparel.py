import json,time
from config import settings
from supplier_client import FjordNansenClient
from importer import parse_product
TARGETS=[["ss8989","https://b2b.fjordnansen.com/product-eng-43620-SAG-XL-bag.html"],["ss8988","https://b2b.fjordnansen.com/product-eng-43619-SAG-MID-bag.html"],["31981-xl","https://b2b.fjordnansen.com/product-eng-23325-FJALAR-XL-compression-sack.html"],["31981-l","https://b2b.fjordnansen.com/product-eng-4192-FJALAR-L-compression-sack.html"]]
def main():
 cfg=settings(); c=FjordNansenClient(cfg["base_url"],cfg["login"],cfg["password"])
 resp,auth=c._authenticate()
 if resp is None or not auth.get("authenticated"): raise RuntimeError(str(auth))
 for key,url in TARGETS:
  r=c.session.get(url,timeout=30); r.raise_for_status()
  row=parse_product(r.text,r.url)
  print("SLEEPACC "+key+" "+json.dumps({"stock":row.get("supplier_stock"),"attrs":row.get("attributes_json")},ensure_ascii=False),flush=True)
  time.sleep(1)
if __name__=="__main__": main()
